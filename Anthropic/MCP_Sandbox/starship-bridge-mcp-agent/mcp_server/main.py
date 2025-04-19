# mcp_server/main.py
import anyio
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp_server.config import Settings # Import the Settings model

# --- Load configuration EARLY ---
# (Keep existing config loading and validation logic here...)
try:
    config = Settings() # This reads .env automatically via pydantic-settings

    # *** Validate DIRECTORY_SANDBOX ***
    if not config.DIRECTORY_SANDBOX:
         raise ValueError("DIRECTORY_SANDBOX is not set in the .env file.")
    sandbox_path = Path(config.DIRECTORY_SANDBOX)
    if not sandbox_path.is_absolute():
         raise ValueError(f"DIRECTORY_SANDBOX '{config.DIRECTORY_SANDBOX}' must be an absolute path.")

    # Create the sandbox directory if it doesn't exist
    sandbox_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Validated and ensured Sandbox Directory exists: {sandbox_path.resolve()}")

except ValueError as e:
     logging.error(f"Configuration Error: {e}")
     exit(1) # Exit if config is invalid
except Exception as e:
     logging.error(f"Unexpected error loading configuration: {e}")
     exit(1)


# --- Initialize FastMCP ---
bridge_mcp_server = FastMCP("StarshipBridgeAgentBackend")


# --- Import tool modules AFTER server instance and config are ready ---
# This ensures the @bridge_mcp_server.tool() decorators run and register the tools
from mcp_server.tools import file_system
from mcp_server.tools import git
from mcp_server.tools import build_deploy
from mcp_server.tools import workspace # <<< ADD THIS LINE

# --- Planned Future Tool Imports (Add as they are implemented) ---
# from mcp_server.tools import aws
# from mcp_server.tools import stripe
# from mcp_server.tools import testing
# from mcp_server.tools import shell


# --- Main Run Function ---
def run():
    # Standard run logic using default stdio transport
    bridge_mcp_server.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()