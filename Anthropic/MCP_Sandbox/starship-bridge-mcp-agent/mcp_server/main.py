# mcp_server/main.py
import anyio
import logging
from pathlib import Path # Add Path import
from mcp.server.fastmcp import FastMCP
from mcp_server.config import Settings # Import the Settings model

# --- Load configuration EARLY ---
try:
    config = Settings() # This reads .env automatically via pydantic-settings

    # *** Validate DIRECTORY_SANDBOX ***
    if not config.DIRECTORY_SANDBOX:
         raise ValueError("DIRECTORY_SANDBOX is not set in the .env file.")
    sandbox_path = Path(config.DIRECTORY_SANDBOX)
    if not sandbox_path.is_absolute():
         # Attempt to resolve relative to the .env file location if needed, but absolute is safer
         # Forcing absolute path for clarity and security:
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
# We don't store config on the server instance directly unless needed via lifespan
bridge_mcp_server = FastMCP("StarshipBridgeAgentBackend")

# --- Import tool modules AFTER server instance and config are ready ---
from mcp_server.tools import file_system, git, build_deploy # Ensure build_deploy is imported
# TODO: Import other tool modules (aws, stripe, workspace) once created

# --- Main Run Function ---
def run():
    # Standard run logic using default stdio transport
    bridge_mcp_server.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Configure logging
    # Set log level from config if desired: logging.basicConfig(level=config.LOG_LEVEL or "INFO")
    run()