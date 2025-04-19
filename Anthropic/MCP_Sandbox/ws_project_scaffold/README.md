# Starship Bridge - Agentic Development Backend (MCP Server)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Welcome, Captain! This is the **MCP Server**, acting as the secure backend and tool provider for your AI agents (like Gemini 1.5/2.5) tasked with software development and deployment.

Think of this as the "engine room" and "tool library" for your AI crew. An external **Orchestration Assistant** (your primary AI interface) connects to this server via an MCP client and uses the tools provided here to execute high-level directives safely.

This server **does not** contain the AI agent logic itself; it **enables** agentic workflows by providing a secure execution environment and specific capabilities.

## Core Functionality

*   **Secure Sandboxing:** All operations (file I/O, git, builds, commands) are strictly contained within isolated workspaces located under the `DIRECTORY_SANDBOX` path defined in the server's `.env` configuration.
*   **MCP Tool Interface:** Exposes capabilities as tools consumable by any MCP-compatible client/agent:
    *   Workspace Management (`core/workspace.py`)
    *   Sandboxed File System Operations (`tools/file_system.py`)
    *   Sandboxed Git Version Control (`tools/git.py`)
    *   Sandboxed Build & Deploy (SAM, Vercel/Coolify) (`tools/build_deploy.py`)
    *   Direct AWS Service Interaction (Boto3) (`tools/aws.py`)
    *   Stripe API Integration (`tools/stripe.py`)
    *   Sandboxed Testing (`tools/testing.py`)
    *   (Limited) Sandboxed Shell Execution (`tools/shell.py`)

## Proposed Directory Structure

starship-bridge-mcp-agent/
├── .env.example # Example env vars (MUST SET DIRECTORY_SANDBOX)
├── .gitignore
├── pyproject.toml # Dependencies (mcp, pydantic-settings, boto3, etc.)
├── README.md # This file
│
└── mcp_server/ # Main Python package for the MCP server
├── init.py
├── main.py # Entry point, FastMCP init, Sandbox Validation
│
├── tools/ # Tool implementations grouped by function
│ ├── init.py
│ ├── file_system.py # Sandboxed file I/O
│ ├── git.py # Sandboxed Git commands
│ ├── build_deploy.py # Sandboxed SAM, Vercel/Coolify
│ ├── aws.py # Boto3 AWS interactions
│ ├── stripe.py # Stripe API interactions
│ ├── testing.py # Sandboxed test execution
│ └── shell.py # (Use cautiously) Sandboxed shell
│
├── resources/ # Optional: MCP resource definitions
│ └── init.py
│
├── prompts/ # Optional: MCP prompt definitions
│ └── init.py
│
├── core/ # Core server logic & helpers
│ ├── init.py
│ ├── workspace.py # Workspace creation/management within sandbox
│ └── security.py # Path validation & sandboxing helpers
│
└── config.py # Loads config from .env via pydantic-settings



## Quickstart & Installation (For Running the MCP Server)

**Prerequisites:**

*   Python 3.10+
*   `uv` (Python package manager: `pip install uv`)
*   Docker (Recommended, required for some tools like `sam build --use-container`)
*   Git CLI
*   AWS CLI (Configured credentials)
*   (Optional) AWS SAM CLI

**Setup:**

1.  **Clone:** `git clone <this-repo-url>`
2.  **Navigate:** `cd starship-bridge-mcp-agent`
3.  **Configure `.env`:**
    *   `cp .env.example .env`
    *   **Edit `.env` and set `DIRECTORY_SANDBOX` to a valid, absolute path.** This is mandatory.
    *   Add necessary API keys/credentials (AWS, Stripe, etc.). **Do not commit `.env`!**
4.  **Install Dependencies:** `uv sync`
5.  **Run Server:** `uv run python mcp_server/main.py`

The server will start (defaulting to `stdio` transport) and wait for client connections.

## Security Considerations

*   The **`DIRECTORY_SANDBOX` is the primary security boundary.** Ensure this path is properly secured on the host system.
*   The `run_shell_command` tool is powerful and should be enabled/used with caution. Prefer specific, typed tools.
*   Handle all API keys and credentials via the `.env` file and secure environment variable practices. They are loaded by the server, not passed in tool arguments.

## Agent Interaction Model

1.  **Captain (You):** Issue high-level commands to your Orchestration Assistant AI.
2.  **Orchestration Assistant (AI):** Connects to this MCP Server via an MCP client. Plans tasks using the available tools.
3.  **MCP Server (This Code):** Executes tool requests within the secure sandbox. Returns results/errors.
4.  **Orchestration Assistant:** Interprets results, continues planning, or reports back.

**Remember:** You are the Captain. Review agent plans and the outputs of tools like `git_diff_staged` before authorizing potentially impactful actions like `git_push` or deployments. Treat the AI as a highly productive but supervised member of your crew.
""" # End of the multi-line string for content

try:
    # Assuming 'mcp_client' is your initialized ClientSession instance
    result = await mcp_client.call_tool(
        "write_file",
        {
            "workspace_id": workspace_id,
            "relative_path": relative_path,
            "content": readme_content,
        }
    )
    # Assuming the tool returns TextContent("true") on success
    if result.content[0].text == 'true':
        print(f"Action: Successfully wrote {relative_path} to workspace {workspace_id}")
    else:
        print(f"Action: Tool 'write_file' reported failure.")

except Exception as e:
    print(f"Action Failed: Error calling write_file tool: {e}")
