
# Core Components

**orchestrator_client.py**: Yes, this is the script that acts as the MCP Client. It's the "controller" or "console" you interact with. It takes your high-level commands, talks to the Gemini model (which does the planning), and sends specific tool execution requests to the MCP Server.

**starship-bridge-mcp-agent/mcp_server/main.py**: Yes, this is the entry point for the MCP Server. It's the "engine room" that runs, listens for client connections, and executes the requested tools (write_file, git_commit, etc.) within the secure sandbox.

**ws_project_scaffold/**: Yes, this is an example workspace directory inside the sandbox (MCP_Sandbox/). This is where the actual project code (like the Next.js app being built or the Lambda function being debugged) lives and is actively modified by the tools being run via the MCP server.

## Where do the task-specific agents go?

This is where the mental model shifts slightly. In this setup, the "agents" aren't separate programs or files in the filesystem.
The "Agent" is the LLM Instance/Session: The primary "agent" doing the planning and reasoning is the Gemini model instance that orchestrator_client.py interacts with. It's given the system prompt defining its role and capabilities (the tools it can use).
"Task-Specific" Behavior via Prompting & Context: You achieve specialization by giving this single Gemini agent specific high-level tasks.
If you tell it, "Refactor the frontend components," it will reason and primarily choose to use read_file, write_file, and maybe run_project_tests targeting the frontend code within the workspace.

If you tell it, "Deploy the backend Lambda," it will reason and choose to use sam_build and sam_deploy targeting the backend code within the workspace.
One Conductor, Many Instruments: Think of orchestrator_client.py as the conductor (interpreting your score), the Gemini session as the lead musician (reading the score and deciding what needs to be played), and the MCP Server tools as the different instruments the musician can pick up and play within the defined stage (MCP_Sandbox/workspace_id). The same musician plays different parts of the symphony using different instruments based on the conductor's direction and the score (system prompt + task).

## Parallelism (If needed later):
Your mention of "agents running in parallel" would typically be implemented by:
Multiple orchestrator_client.py Instances: Running several copies of the client script, each potentially working in a different workspace_id but connecting to the same MCP Server. Each instance manages its own independent Gemini session.
Advanced orchestrator_client.py: Modifying the client script to use asyncio to manage multiple concurrent conversations with Gemini and potentially multiple concurrent tool calls to the MCP server (if the server and tools are thread-safe/async-safe).
For now, the simplest model is one orchestrator_client.py managing one Gemini session, which intelligently selects tools from the single MCP server based on the task you give it.

**Level 0**: Your Host Machine
This is where you run everything initially.
Contains the MCP_Sandbox directory.

**Level 1**: The Sandbox Root & The Tool Server Code
Inside MCP_Sandbox, you have:

**.env**: Configures the sandbox root itself.

**starship-bridge-mcp-agent/**: The code for the MCP Server. This is the "engine room" that provides the tools and enforces the sandbox rules. It defines write_file, git_commit, etc.

NOTE: The MCP Server process runs from this starship-bridge-mcp-agent directory (or referencing it).

**Level 2**: The Agent's Workspace (Dynamic)
Inside MCP_Sandbox (the path defined in the server's .env), the MCP Server's create_workspace tool (once implemented) will create directories like ws_project_scaffold/, ws_lambda_debug_task/, etc.
These workspace directories contain the target code the agent is actually working on (e.g., the cloned unbias3d repo, the generated Next.js files, the Lambda function code).
ws_project_scaffold/README.md is an example of a file created by the agent using a tool (write_file) within its designated workspace.

**Level 3**: The Orchestrator Client (Controller)
orchestrator_client.py is the script that you run to interact with the Gemini agent (the "Orchestration Assistant").
This script acts as the controller. It holds the system prompt, communicates with the Gemini API, parses responses, and uses an MCP Client library to send commands to the running MCP Server.

It needs to exist outside the agent's dynamic workspaces (ws_project_scaffold, etc.) because:

It manages the lifecycle of potentially multiple workspaces.

It shouldn't be accidentally deleted or modified by the agent working within a specific workspace (imagine the agent running git clean -fdx inside its workspace!).
Logically, you might place orchestrator_client.py directly inside MCP_Sandbox/ (alongside starship-bridge-mcp-agent/) or even in a completely separate directory on your host machine. Its location just needs to allow it to find and start/connect to the MCP Server process.

## Analogy:

MCP_Sandbox: The secured factory floor.

starship-bridge-mcp-agent: The factory's fixed machinery (robots, conveyor belts = MCP Server + Tools).

ws_project_scaffold: A specific project assembly area on the factory floor.

orchestrator_client.py: The control room console outside the factory floor, from which you send instructions to the machinery to work on projects in the assembly areas.

