
# Starship Bridge - Agentic Development System (LLM_tools Root)

## Overview

Welcome to the `LLM_tools` project, Captain! This repository contains the components for **Starship Bridge**, an experimental agentic software development system.

The core system resides within the `Anthropic/MCP_Sandbox` directory and consists of:

1.  **Orchestration Assistant Client (`orchestrator/client.py`):** A Python client that interacts with you (the Captain) and a Large Language Model (like Google's Gemini). It plans tasks based on your high-level goals and uses the MCP Server's tools for execution.
2.  **MCP Server (`starship-bridge-mcp-agent/`):** A secure Python backend built with `mcp-sdk`. It provides specific, sandboxed tools (file system, git, build/deploy, etc.) over the MCP protocol. All operations are restricted to designated workspace subdirectories within a configured sandbox path.
3.  **MCP Library (`Anthropic/python-sdk/`):** The source code for the `mcp-sdk` library used by both the client and server.

The goal is to enable the Orchestrator to manage complex software development workflows (e.g., code migration, debugging, deployment, API integration) safely and effectively by leveraging the specialized tools provided by the MCP Server.

## Project Structure Highlights
```
LLM_tools/
├── Anthropic/
│   ├── MCP_Sandbox/             # <-- Primary working directory
│   │   ├── .env.example         # Example environment variables
│   │   ├── .env                 # **Your local config (MUST CREATE & CONFIGURE)**
│   │   ├── orchestrator/        # Orchestration Assistant Client code
│   │   │   ├── client.py        # Main client script
│   │   │   ├── agents/          # Agent definitions (e.g., McKinsey Solver)
│   │   │   └── prompt_generators/ # Prompt generation utilities
│   │   ├── starship-bridge-mcp-agent/ # MCP Server code
│   │   │   ├── mcp_server/      # Server package
│   │   │   │   ├── main.py      # Server entrypoint
│   │   │   │   ├── config.py    # Config loading
│   │   │   │   ├── core/        # Security, workspace management
│   │   │   │   └── tools/       # Tool implementations (FS, Git, etc.)
│   │   │   └── pyproject.toml   # Server-specific metadata (if needed)
│   │   └── ws_.../              # Dynamically created workspace directories
│   ├── python-sdk/              # MCP Library source code
│   └── ...
├── requirements.txt             # Python dependencies for the project
├── README.md                    # This file
└── ...
```

## Prerequisites

*   **Python:** 3.10+
*   **uv:** Modern Python package installer and runner (`pip install uv` or follow official instructions). Used for installing dependencies and running the server/client efficiently.
*   **Git:** Command-line tool required for `git` tools on the MCP Server.
*   **Docker:** Recommended, required for certain tools like `sam build --use-container`. Ensure Docker Desktop/Engine is running.
*   **AWS CLI (Optional but Recommended):** For manual AWS checks and needed if `sam` or `aws` tools are used. Configure with your credentials (`aws configure`).
*   **AWS SAM CLI (Optional):** Required for `sam build`/`sam deploy` tools.
*   **API Keys:**
    *   Google Gemini API Key
    *   AWS Credentials (accessible via environment or configured CLI profile)
    *   Stripe API Keys (if using Stripe tools)
    *   (Potentially others for Vercel, etc.)

## Quickstart Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url> LLM_tools
    cd LLM_tools
    ```

2.  **Install `uv`:**
    If you don't have `uv` installed:
    ```bash
    pip install uv
    # Or follow official uv install guide: https://github.com/astral-sh/uv
    ```

3.  **Navigate to Sandbox:**
    All subsequent commands should typically be run from this directory:
    ```bash
    cd Anthropic/MCP_Sandbox
    ```

4.  **Configure Environment (`.env`):**
    *   Copy the example: `cp .env.example .env`
    *   **CRITICAL:** Edit the `.env` file:
        *   **Set `DIRECTORY_SANDBOX`:** Provide a **valid, absolute path** on your machine where the MCP Server will create workspaces and operate. This directory **must** exist or be creatable by the server process. E.g., `DIRECTORY_SANDBOX=/Users/YourUser/Workspaces/StarshipBridgeSandbox`. **Ensure this location is secure and dedicated.**
        *   Add your `GEMINI_API_KEY`.
        *   Add `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (or ensure your environment/AWS profile is configured correctly for Boto3/SAM).
        *   Add `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` if needed.
    *   **DO NOT COMMIT your `.env` file!**

5.  **Install Dependencies:**
    From the `LLM_tools` root directory (where `requirements.txt` is):
    ```bash
    # Use uv to create a virtual environment and install dependencies
    uv venv  # Creates .venv directory
    uv pip sync requirements.txt # Installs dependencies from requirements.txt into .venv
    source .venv/bin/activate # Activate the virtual environment (Linux/macOS)
    # For Windows: .venv\Scripts\activate
    ```
    *Alternatively, if you prefer running directly without explicitly activating:*
    ```bash
    # From LLM_tools directory:
    uv pip sync requirements.txt
    ```
    (But using a venv is recommended)


## Running the System

You'll need **two separate terminal windows/tabs**, both navigated to the `LLM_tools/Anthropic/MCP_Sandbox` directory and with the virtual environment activated (if you created one).

**Terminal 1: Start the MCP Server**

```bash
# Ensure you are in LLM_tools/Anthropic/MCP_Sandbox
# Run using uv (it will find the code inside starship-bridge-mcp-agent)
uv run python ./starship-bridge-mcp-agent/mcp_server/main.py
```
The server will start, log its initialization (including the Sandbox Directory validation), and wait for a client connection via stdio.

**Terminal 2: Start the Orchestrator Client**

```bash
# Ensure you are in LLM_tools/Anthropic/MCP_Sandbox
# Run the client script
python ./orchestrator/client.py
```
The client will attempt to start and connect to the MCP server process it spins up. You should see connection logs, followed by the "Captain Problem:" prompt.

## Basic Workflow

1.  Enter a high-level goal or problem at the "Captain Problem:" prompt in the Orchestrator Client terminal.
2.  The Orchestrator uses its prompt generators and the McKinsey Solver Agent (via Gemini) to create an initial plan.
3.  The Orchestrator *should* request to use the `create_workspace` tool first.
4.  It will then proceed to call other MCP tools (like `git_clone`, `write_file`, `sam_build`, etc.) based on its plan.
5.  Tool execution happens via the MCP Server (Terminal 1), operating within the created workspace inside the `DIRECTORY_SANDBOX`.
6.  Results and status are reported back to the Orchestrator (Terminal 2), which interacts with Gemini to continue the process or report back to you.

## Security

*   The `DIRECTORY_SANDBOX` is the cornerstone of security. All tool operations are confined within workspaces under this path. **Choose this location carefully.**
*   API Keys and sensitive credentials should **only** be stored in the `.env` file (which is gitignored) and accessed by the **MCP Server** configuration loader. Do not pass secrets directly in tool parameters.
*   Review the agent's plans and tool outputs (especially `git diff` results) before approving destructive or external actions like `git push` or `sam deploy`.

## License

(Assumed MIT based on example file - Replace if different)
Licensed under the MIT License. See LICENSE file for details.