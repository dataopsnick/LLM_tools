import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
from dotenv import load_dotenv

# MCP Client Imports (assuming mcp package is installed)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as mcp_types

# Local Imports (adjust paths if structure differs)
from prompt_generators.loader import load_prompt_generators, SimplePromptGeneratorFunc
from agents.mckinsey_solver import McKinseySolutionPlan, MCKINSEY_SYSTEM_PROMPT

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OrchestratorClient")
# Load .env file from the directory where *this script* runs (e.g., MCP_Sandbox/)
# Make sure your .env file is in MCP_Sandbox/
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Load API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# MCP Server Configuration
MCP_SERVER_PROJECT_DIR = "./starship-bridge-mcp-agent" # Relative path to the server project
MCP_SERVER_COMMAND = "uv"
MCP_SERVER_ARGS = ["run", "python", "mcp_server/main.py"]

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)
# Using a model that supports longer context and JSON mode potentially
# Update model name as needed (e.g., 'gemini-1.5-pro-latest')
gemini_model_name = 'gemini-1.5-flash' # Or 'gemini-1.5-pro'
gemini_model = genai.GenerativeModel(gemini_model_name)
logger.info(f"Using Gemini Model: {gemini_model_name}")

# --- Load Prompt Generators ---
# Assumes generators are in orchestrator/prompt_generators/
prompt_generator_functions: Dict[str, SimplePromptGeneratorFunc] = load_prompt_generators()
if not prompt_generator_functions:
     logger.warning("No prompt generators loaded. The McKinsey agent might not receive diverse input.")

# --- Main Orchestration Loop ---
async def main():
    logger.info("Starting Orchestration Assistant Client...")
    mcp_server_process = None # Initialize to None

    try:
        # --- Start MCP Server ---
        logger.info(f"Starting MCP Server process: {MCP_SERVER_COMMAND} {' '.join(MCP_SERVER_ARGS)} in {MCP_SERVER_PROJECT_DIR}")
        mcp_server_process = await asyncio.create_subprocess_exec(
            MCP_SERVER_COMMAND, *MCP_SERVER_ARGS,
            cwd=MCP_SERVER_PROJECT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.info(f"MCP Server process started (PID: {mcp_server_process.pid}). Waiting briefly...")
        await asyncio.sleep(7) # Increased wait time

        # --- Connect MCP Client ---
        server_params = StdioServerParameters(
            command=MCP_SERVER_COMMAND, args=MCP_SERVER_ARGS, cwd=MCP_SERVER_PROJECT_DIR,
            env=os.environ.copy() # Pass current environment
        )
        async with stdio_client(server_params) as streams:
            read_stream, write_stream = streams
            async with ClientSession(read_stream, write_stream) as mcp_session:
                logger.info("MCP Client connecting...")
                try:
                    init_result = await mcp_session.initialize()
                    logger.info(f"MCP Client initialized with server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
                except Exception as e:
                    logger.error(f"MCP initialization failed: {e}")
                    # Attempt to get server logs
                    try:
                         stdout, stderr = await asyncio.wait_for(mcp_server_process.communicate(), timeout=2.0)
                         logger.error(f"MCP Server stdout:\n{stdout.decode(errors='ignore')}")
                         logger.error(f"MCP Server stderr:\n{stderr.decode(errors='ignore')}")
                    except asyncio.TimeoutError:
                         logger.error("Timed out waiting for MCP server logs.")
                    except Exception as log_err:
                         logger.error(f"Error getting MCP server logs: {log_err}")
                    return # Exit if connection fails

                # --- Interaction Loop ---
                print("\n--- Starship Bridge Orchestrator ---")
                print("Enter the core problem/goal you want to analyze.")

                while True:
                    captain_problem = input("\nCaptain Problem: ")
                    if captain_problem.lower() in ["quit", "exit"]:
                        break

                    logger.info(f"Received problem: {captain_problem}")
                    print("Orchestrator: Generating multi-perspective analysis prompts...")

                    # --- Parallel Prompt Generation ---
                    tasks = []
                    for name, func in prompt_generator_functions.items():
                        # Create task to call the generator function
                        # Use asyncio.to_thread if generators are synchronous and potentially blocking
                        # Assuming simple string formatting is fast enough for direct await here
                        tasks.append(asyncio.create_task(run_prompt_generator(name, func, captain_problem)))

                    # Wait for all prompt generator tasks to complete
                    generated_prompts: List[Tuple[str, str | None]] = await asyncio.gather(*tasks)

                    # --- Synthesize Input for McKinsey Agent ---
                    mckinsey_input_parts = []
                    successful_generators = 0
                    for name, prompt_str in generated_prompts:
                         if prompt_str:
                              mckinsey_input_parts.append(f"--- Analysis from {name.replace('_', ' ').title()} Perspective ---\n{prompt_str}\n")
                              successful_generators += 1
                         else:
                              mckinsey_input_parts.append(f"--- Analysis from {name.replace('_', ' ').title()} Perspective ---\nError during generation.\n")

                    if successful_generators == 0:
                         print("Orchestrator: ERROR - Failed to generate input from any perspective.")
                         continue

                    full_mckinsey_input = f"Comprehensive analysis input for problem '{captain_problem}':\n\n" + "\n".join(mckinsey_input_parts)
                    logger.info(f"Synthesized input for McKinsey Agent (length: {len(full_mckinsey_input)} chars)")
                    # logger.debug(f"Full Input:\n{full_mckinsey_input}") # Optional: log full input if needed

                    print(f"Orchestrator: Synthesized input from {successful_generators} perspectives. Invoking McKinsey Solver Agent...")

                    # --- Invoke McKinsey Solver Agent ---
                    try:
                         # Use Gemini API - potentially request JSON output if model supports it well
                         # Note: Adjust generation_config for JSON if using Pro model and it's reliable
                         generation_config = genai.types.GenerationConfig(
                              # response_mime_type="application/json" # Uncomment if using Pro and JSON mode is reliable
                              temperature=0.5 # Adjust as needed
                         )
                         mckinsey_response = await gemini_model.generate_content_async(
                              [MCKINSEY_SYSTEM_PROMPT, full_mckinsey_input],
                              generation_config=generation_config,
                         )

                         response_text = mckinsey_response.text
                         logger.info("Received response from McKinsey Solver Agent.")
                         # logger.debug(f"McKinsey Agent Raw Response:\n{response_text}") # Optional

                         # --- Parse and Validate Output ---
                         # Attempt to parse JSON (may need cleanup if not using strict JSON mode)
                         cleaned_json_text = response_text.strip().replace('```json', '').replace('```', '')
                         plan_data = json.loads(cleaned_json_text)
                         mckinsey_plan = McKinseySolutionPlan.model_validate(plan_data)

                         print("\n--- McKinsey Solution Plan ---")
                         print(mckinsey_plan.model_dump_json(indent=2))
                         print("-----------------------------")
                         print("\nOrchestrator: Plan generated. Ready for next command or execution approval.")
                         # TODO: Add logic here to ask Captain for approval and then
                         # use mcp_session.call_tool to execute steps from the plan

                    except json.JSONDecodeError as e:
                         logger.error(f"Failed to decode JSON from McKinsey Agent: {e}")
                         print(f"Orchestrator: ERROR - Could not parse the plan from the McKinsey Agent. Raw response:\n{response_text}")
                    except Exception as e:
                         logger.error(f"Error during McKinsey Agent interaction: {e}", exc_info=True)
                         print(f"Orchestrator: ERROR - An error occurred while generating the plan: {e}")


    except Exception as e:
         logger.exception(f"Orchestrator client encountered an unhandled error: {e}")
    finally:
        # --- Shutdown ---
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
                 logger.info("MCP Server process already terminated.")
        logger.info("Orchestration Assistant Client shutting down.")


async def run_prompt_generator(name: str, func: SimplePromptGeneratorFunc, problem: str) -> Tuple[str, str | None]:
    """Runs a single generator function, handling errors."""
    try:
        # Assuming generator funcs are synchronous - wrap if they become async
        prompt = func(problem)
        return name, prompt
    except Exception as e:
        logger.error(f"Error running prompt generator '{name}': {e}")
        return name, None # Return None on error


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Orchestration client interrupted by user.")