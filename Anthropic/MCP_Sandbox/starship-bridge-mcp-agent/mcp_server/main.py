# mcp_server/main.py (Simplified Example)
import anyio
import logging
from mcp.server.fastmcp import FastMCP
from mcp_server.config import Settings # Import your Settings model
from mcp_server.tools import file_system, git

# Load configuration EARLY
try:
    config = Settings() # This reads .env automatically
    # *** Add validation for DIRECTORY_SANDBOX here ***
    if not config.DIRECTORY_SANDBOX or not Path(config.DIRECTORY_SANDBOX).is_absolute():
         raise ValueError("DIRECTORY_SANDBOX is missing or not an absolute path in .env")
    # Potentially create the directory if it doesn't exist
    Path(config.DIRECTORY_SANDBOX).mkdir(parents=True, exist_ok=True)
    logging.info(f"Validated Sandbox Directory: {config.DIRECTORY_SANDBOX}")
except ValueError as e:
     logging.error(f"Configuration Error: {e}")
     exit(1) # Exit if config is invalid


# Initialize FastMCP - make config accessible if needed by tools
bridge_mcp_server = FastMCP("StarshipBridgeAgentBackend")
# You might store config on the server instance or pass via lifespan

# --- Import tool modules AFTER server instance is created ---
# --- so the @bridge_mcp_server.tool() decorators work ---
from mcp_server.tools import file_system, git, sam # etc.

# --- Lifespan example to pass config ---
# from collections.abc import AsyncIterator
# from contextlib import asynccontextmanager
# @asynccontextmanager
# async def bridge_lifespan(server: FastMCP) -> AsyncIterator[Settings]:
#      # Perform startup actions
#      yield config # Make config available via context.request_context.lifespan_context
#      # Perform shutdown actions
# bridge_mcp_server.settings.lifespan = bridge_lifespan
# Now tools could potentially access config via ctx.request_context.lifespan_context


def run():
    # Standard run logic
    bridge_mcp_server.run() # Defaults to stdio

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Configure logging
    run()
