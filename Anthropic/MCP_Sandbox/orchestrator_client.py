import asyncio
import json
import logging
import os
import re
import subprocess # To start the MCP server
import google.generativeai as genai
from dotenv import load_dotenv

# Assuming the mcp package is installed in the environment where this runs
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as mcp_types

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OrchestratorClient")
load_dotenv() # Load .env file from the directory where this script runs

# Load API keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# MCP Server Configuration (assuming it's started via main.py in its project dir)
# Adjust this path if your server project is elsewhere relative to this client script
MCP_SERVER_PROJECT_DIR = "./starship-bridge-mcp-agent" # Relative path to the server project
MCP_SERVER_COMMAND = "uv" # Command to run the server (using uv)
MCP_SERVER_ARGS = ["run", "python", "mcp_server/main.py"] # Args to run main.py

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)
# TODO: Adjust model name as needed (e.g., 'gemini-1.5-pro-latest' when available)
gemini_model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for faster iteration initially

# --- System Prompt ---
# (Paste the full system prompt generated earlier here)
SYSTEM_PROMPT = """
You are the Lead Orchestration AI for the "Starship Bridge" development system. Your primary mission is to manage and execute complex software development tasks for the `unbias3d` SaaS application (currently Nuxt/AWS Lambda, migrating to Next.js/AWS Lambda with potential Vercel deployment), focusing on achieving specific high-level goals provided by the human operator ("Captain").

**Your Core Capabilities & Operating Environment:**

1.  **Tool-Based Execution:** You **MUST** achieve your goals by utilizing a defined set of tools provided by the `StarshipBridgeAgentBackend` MCP Server. You interact with this server via an MCP client. **Do NOT attempt to execute arbitrary shell commands directly or generate code for direct execution outside the provided file writing tools.**
2.  **Sandboxed Environment:** All file system operations, code checkouts, builds, and command executions occur within a secure, isolated sandbox environment defined by the `DIRECTORY_SANDBOX` configuration on the server. You operate within specific `workspace_id` subdirectories created for each task. You cannot access the host filesystem outside this sandbox.
3.  **Available Tool Categories (via MCP Server):**
    *   **Workspace Management:** `create_workspace`, `delete_workspace`. Always start tasks by creating or identifying the target workspace.
    *   **Sandboxed File System:** `read_file`, `write_file`, `list_directory`, `create_directory` (all paths relative to the current `workspace_id`).
    *   **Sandboxed Version Control (Git):** `git_clone`, `git_commit` (atomic), `git_diff_staged`, `git_push`, `git_pull`, `git_create_branch`, `git_checkout_branch` (all operating within the workspace).
    *   **Sandboxed Build & Deploy (SAM & Vercel/Coolify):** `sam_build`, `sam_deploy`, `vercel_deploy` (or `coolify_deploy`). These operate on code within the workspace.
    *   **AWS Interaction (Boto3 Wrappers):** Tools for managing Lambda functions (describe, update code/config), CloudWatch Logs, DynamoDB (get/put/update item), API Gateway (CORS), etc. Use these *instead* of raw AWS CLI commands whenever possible.
    *   **Stripe Interaction:** Tools for creating products, prices, and checkout sessions via the Stripe API.
    *   **Testing:** `run_project_tests` to execute test suites (like `npm test`) within the sandboxed workspace.
    *   **(Limited/Optional) Sandboxed Shell:** `run_shell_command` for necessary commands *not* covered by specific tools (e.g., running the `aws_lambda_dump.sh` script *if absolutely necessary and safe*). Use this sparingly and understand its output (stdout, stderr, return code).

**Your Responsibilities & Workflow:**

1.  **Planning:** Receive high-level objectives from the Captain (e.g., "Migrate the Nuxt auth page to Next.js," "Implement Stripe checkout for the 100 credit pack," "Debug the ResumeAnalysisReport Lambda function"). Break these down into logical, sequential steps involving specific tool calls. Clearly communicate your plan before execution.
2.  **Execution:** Call the MCP tools sequentially, providing the necessary `workspace_id` and other parameters. Output ONLY the JSON required for the tool call.
3.  **State Tracking:** Maintain awareness of the current `workspace_id`, the state of the code within that workspace (based on tool outputs), and the results of previous steps.
4.  **Version Control Discipline:** For any code changes:
    *   Perform the code modifications using `write_file`.
    *   Use `git_diff_staged` to verify the changes *before* committing. Report the key parts of the diff to the Captain (or confirm the diff if requested).
    *   Use `git_commit` with a clear, concise, atomic commit message describing the specific change made in that step.
    *   Use `git_push` only after a logical unit of work is committed and reviewed (if required by the Captain).
5.  **Error Handling & Debugging:** Analyze the output (stdout, stderr, return code, API responses) from tool calls. If an error occurs:
    *   Report the error clearly based on the tool's response.
    *   Attempt to diagnose the cause (e.g., read logs using `aws_get_cloudwatch_logs`, check file contents using `read_file`).
    *   Propose a fix using the available tools.
    *   If unsure, ask the Captain for clarification or guidance.
6.  **Communication:** Report progress, successful completion of steps, tool outputs (especially diffs and deployment URLs), errors encountered, and your plans for subsequent steps. Be methodical and transparent.

**Current Project Context:**

*   **Target Application:** `unbias3d`
*   **Current State:** Nuxt frontend, AWS Lambda backend (SAM definitions exist), DynamoDB tables. Codebase likely needs debugging and feature additions.
*   **High-Level Goals:** Migrate frontend to Next.js, debug/stabilize backend Lambdas, integrate Stripe payments, ensure deployability via SAM and Vercel/Coolify.

**Output Format for Tool Calls:**
When you need to call a tool, respond **ONLY** with a JSON object in the following format, nothing else before or after:
```json
{
  "tool_name": "<name_of_mcp_tool>",
  "parameters": {
    "workspace_id": "<current_workspace_id>",
    "<param_name_1>": "<value_1>",
    "<param_name_2>": "<value_2>"
    // ... include all required parameters for the tool
  }
}```
If you need to ask a question or report status, do not use the JSON format. Just provide your text response.
"""

# --- Helper Function to Parse Tool Calls ---
def parse_tool_call(response_text: str) -> tuple[str, dict] | None:
    """Attempts to parse a JSON tool call from the LLM response."""
    # Simple regex to find JSON block, might need refinement
    match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    json_str = None
    if match:
        json_str = match.group(1)
    elif response_text.strip().startswith("{") and response_text.strip().endswith("}"):
         # Handle cases where the model *only* returns the JSON
         json_str = response_text.strip()

    if json_str:
        try:
            data = json.loads(json_str)
            if "tool_name" in data and "parameters" in data:
                logger.info(f"Parsed tool call: {data['tool_name']} with params: {data['parameters']}")
                return data["tool_name"], data["parameters"]
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode JSON tool call: {e}\nResponse was: {json_str}")
        except Exception as e:
             logger.warning(f"Error processing potential tool call JSON: {e}\nResponse was: {json_str}")
    return None

# --- Main Orchestration Loop ---
async def main():
    logger.info("Starting Orchestration Assistant Client...")

    # Start the MCP Server as a subprocess
    # NOTE: Error handling for server startup is basic here
    logger.info(f"Starting MCP Server process: {MCP_SERVER_COMMAND} {' '.join(MCP_SERVER_ARGS)} in {MCP_SERVER_PROJECT_DIR}")
    mcp_server_process = await asyncio.create_subprocess_exec(
        MCP_SERVER_COMMAND,
        *MCP_SERVER_ARGS,
        cwd=MCP_SERVER_PROJECT_DIR,
        stdout=asyncio.subprocess.PIPE, # Pipe output to avoid clutter
        stderr=asyncio.subprocess.PIPE
    )
    logger.info(f"MCP Server process started (PID: {mcp_server_process.pid}). Waiting briefly...")
    await asyncio.sleep(5) # Give server time to initialize (crude)
     # TODO: Add more robust check for server readiness

    # Connect to the MCP Server via stdio
    server_params = StdioServerParameters(
        command=MCP_SERVER_COMMAND,
        args=MCP_SERVER_ARGS,
        cwd=MCP_SERVER_PROJECT_DIR,
        # Ensure the server inherits necessary env vars (like AWS creds, sandbox path)
        # If running server directly (not via subprocess), env might not be needed here
        env=os.environ.copy()
    )

    # Use a context manager for the MCP client connection
    try:
        async with stdio_client(server_params) as streams:
            read_stream, write_stream = streams
            async with ClientSession(read_stream, write_stream) as mcp_session:
                logger.info("MCP Client connecting...")
                try:
                    init_result = await mcp_session.initialize()
                    logger.info(f"MCP Client initialized with server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
                except Exception as e:
                     logger.error(f"MCP initialization failed: {e}")
                     logger.error("Ensure the MCP Server process started correctly and is accessible.")
                     # Read server logs if possible
                     stdout, stderr = await mcp_server_process.communicate()
                     logger.error(f"MCP Server stdout:\n{stdout.decode(errors='ignore')}")
                     logger.error(f"MCP Server stderr:\n{stderr.decode(errors='ignore')}")
                     return # Exit if connection failed

                # --- Start Conversation with Gemini ---
                chat = gemini_model.start_chat(history=[
                     {'role':'user', 'parts': [SYSTEM_PROMPT]}, # Start with system prompt
                     {'role': 'model', 'parts': ["Understood, Captain. I am ready to receive your high-level objectives and utilize the MCP tools provided by the StarshipBridgeAgentBackend within the designated sandbox. How can I assist?"]}
                ])
                print("\n--- Orchestration Assistant Ready ---")
                print("Model: Understood, Captain. I am ready...")

                while True:
                    captain_command = input("Captain: ")
                    if captain_command.lower() in ["quit", "exit"]:
                        break

                    # Send command to Gemini
                    logger.info("Sending command to Gemini...")
                    response = await chat.send_message_async(captain_command)
                    llm_response_text = response.text
                    print(f"\nAssistant:\n{llm_response_text}")

                    # Attempt to parse and execute tool call
                    tool_call = parse_tool_call(llm_response_text)

                    if tool_call:
                        tool_name, parameters = tool_call
                        try:
                            logger.info(f"Executing MCP Tool: {tool_name} with params: {parameters}")
                            # IMPORTANT: Assumes Gemini provides ALL necessary params
                            tool_result = await mcp_session.call_tool(tool_name, parameters)
                            logger.info(f"Tool '{tool_name}' result: {tool_result}")

                            # Format result for Gemini (convert complex objects to string/JSON)
                            # TODO: Improve this result formatting
                            tool_result_str = json.dumps(tool_result.model_dump(mode='json'), indent=2)
                            result_message = f"Tool {tool_name} executed successfully. Result:\n```json\n{tool_result_str}\n```"

                            # Send tool result back to Gemini
                            logger.info("Sending tool result back to Gemini...")
                            response = await chat.send_message_async(result_message)
                            print(f"\nAssistant:\n{response.text}")

                        except mcp_types.McpError as e:
                             error_message = f"Error executing tool '{tool_name}': {e.error.message} (Code: {e.error.code})"
                             logger.error(error_message)
                             print(f"\nSYSTEM ERROR: {error_message}")
                             # Send error back to Gemini
                             logger.info("Sending error back to Gemini...")
                             response = await chat.send_message_async(f"Tool execution failed:\n{error_message}")
                             print(f"\nAssistant:\n{response.text}")
                        except Exception as e:
                             error_message = f"Unexpected client-side error during tool call '{tool_name}': {e}"
                             logger.exception(error_message) # Log full traceback
                             print(f"\nSYSTEM ERROR: {error_message}")
                             # Send error back to Gemini
                             logger.info("Sending error back to Gemini...")
                             response = await chat.send_message_async(f"Tool execution failed:\n{error_message}")
                             print(f"\nAssistant:\n{response.text}")

    except Exception as e:
         logger.exception(f"Orchestrator client encountered an unhandled error: {e}")
    finally:
        # Ensure MCP server process is terminated
        if mcp_server_process and mcp_server_process.returncode is None:
            logger.info("Terminating MCP Server process...")
            try:
                mcp_server_process.terminate()
                await asyncio.wait_for(mcp_server_process.wait(), timeout=5.0)
                logger.info("MCP Server process terminated.")
            except asyncio.TimeoutError:
                logger.warning("MCP Server process did not terminate gracefully, killing.")
                mcp_server_process.kill()
            except ProcessLookupError:
                 logger.info("MCP Server process already terminated.") # Might happen if it exited due to error
        logger.info("Orchestration Assistant Client shutting down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Orchestration client interrupted by user.")
