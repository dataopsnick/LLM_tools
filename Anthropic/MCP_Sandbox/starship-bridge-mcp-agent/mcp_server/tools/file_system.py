# mcp_server/tools/file_system.py
import logging
from pathlib import Path
from typing import TYPE_CHECKING

# Assuming FastMCP instance is created in main.py and accessible
# You might need to adjust how 'bridge_mcp_server' and 'config' are accessed
# depending on your project structure (e.g., passing them around, using globals - careful!)
# For simplicity, let's assume they are accessible here.
# A better approach is often dependency injection via the lifespan context.
from mcp_server.main import bridge_mcp_server, config # Adjust import as needed
from mcp_server.core.security import resolve_and_validate_path, SandboxViolationError

if TYPE_CHECKING:
    from mcp_server.config import Settings

logger = logging.getLogger(__name__)

@bridge_mcp_server.tool()
def write_file(workspace_id: str, relative_path: str, content: str) -> bool:
    """
    Writes text content to a specified file within the agent's sandboxed workspace.
    Creates parent directories if they don't exist. Overwrites the file if it exists.

    Args:
        workspace_id: The unique ID of the current agent workspace.
        relative_path: The path to the file, relative to the workspace root.
                       Must not contain '..' or attempt to escape the workspace.
        content: The text content to write to the file.

    Returns:
        True if the write was successful.

    Raises:
        ValueError: If workspace_id or relative_path are invalid.
        SandboxViolationError: If the path attempts to go outside the designated workspace.
        IOError: If there's an error writing the file.
    """
    logger.info(f"Attempting to write file '{relative_path}' in workspace '{workspace_id}'")
    try:
        # Resolve and validate the path *within* the specific workspace sandbox
        # Pass the loaded config object to the validator
        absolute_path = resolve_and_validate_path(
            config=config, # Pass loaded config here
            workspace_id=workspace_id,
            relative_path=relative_path,
            ensure_parent_exists=True # Create parent dirs for the file
        )

        # Write the content
        absolute_path.write_text(content, encoding='utf-8')
        logger.info(f"Successfully wrote to {absolute_path}")
        return True

    except (ValueError, SandboxViolationError) as sec_err:
        logger.error(f"Security error writing file: {sec_err}")
        raise # Re-raise security errors to be handled by the server/client
    except IOError as io_err:
        logger.error(f"IO error writing file {relative_path} in {workspace_id}: {io_err}")
        # Depending on desired behavior, you might return False or raise
        raise IOError(f"Failed to write file: {io_err}")
    except Exception as e:
        logger.exception(f"Unexpected error writing file {relative_path} in {workspace_id}: {e}")
        raise # Re-raise unexpected errors

# --- TODO: Add implementations for read_file, list_directory, create_directory ---
# --- using the same resolve_and_validate_path helper function ---

@bridge_mcp_server.tool()
def read_file(workspace_id: str, relative_path: str) -> str:
    """
    Reads text content from a specified file within the agent's sandboxed workspace.

    Args:
        workspace_id: The unique ID of the current agent workspace.
        relative_path: The path to the file, relative to the workspace root.

    Returns:
        The content of the file as a string.

    Raises:
        ValueError: If workspace_id or relative_path are invalid.
        SandboxViolationError: If the path attempts to go outside the workspace.
        FileNotFoundError: If the file does not exist at the specified path.
        IOError: If there's an error reading the file.
    """
    logger.info(f"Attempting to read file '{relative_path}' in workspace '{workspace_id}'")
    try:
        absolute_path = resolve_and_validate_path(
            config=config,
            workspace_id=workspace_id,
            relative_path=relative_path,
            check_existence=True # Ensure the file exists before reading
        )

        if not absolute_path.is_file():
             raise FileNotFoundError(f"Path exists but is not a file: {absolute_path}")

        content = absolute_path.read_text(encoding='utf-8')
        logger.info(f"Successfully read file {absolute_path}")
        return content

    except (ValueError, SandboxViolationError, FileNotFoundError) as err:
        logger.error(f"Error reading file: {err}")
        raise # Re-raise known errors
    except IOError as io_err:
        logger.error(f"IO error reading file {relative_path} in {workspace_id}: {io_err}")
        raise IOError(f"Failed to read file: {io_err}")
    except Exception as e:
        logger.exception(f"Unexpected error reading file {relative_path} in {workspace_id}: {e}")
        raise

@bridge_mcp_server.tool()
def list_directory(workspace_id: str, relative_path: str = ".") -> list[str]:
    """
    Lists the contents (files and directories) of a specified directory within
    the agent's sandboxed workspace.

    Args:
        workspace_id: The unique ID of the current agent workspace.
        relative_path: The path to the directory, relative to the workspace root.
                       Defaults to the workspace root itself (".").

    Returns:
        A list of filenames and directory names within the specified path.

    Raises:
        ValueError: If workspace_id or relative_path are invalid.
        SandboxViolationError: If the path attempts to go outside the workspace.
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path exists but is not a directory.
    """
    logger.info(f"Attempting to list directory '{relative_path}' in workspace '{workspace_id}'")
    try:
        # Resolve and validate the directory path, ensuring it exists
        absolute_path = resolve_and_validate_path(
            config=config,
            workspace_id=workspace_id,
            relative_path=relative_path,
            check_existence=True # Ensure the directory exists
        )

        if not absolute_path.is_dir():
            raise NotADirectoryError(f"Path exists but is not a directory: {absolute_path}")

        # List directory contents
        contents = [item.name for item in absolute_path.iterdir()]
        logger.info(f"Successfully listed directory {absolute_path}")
        return contents

    except (ValueError, SandboxViolationError, FileNotFoundError, NotADirectoryError) as err:
        logger.error(f"Error listing directory: {err}")
        raise # Re-raise known errors
    except Exception as e:
        logger.exception(f"Unexpected error listing directory {relative_path} in {workspace_id}: {e}")
        raise

@bridge_mcp_server.tool()
def create_directory(workspace_id: str, relative_path: str) -> bool:
    """
    Creates a directory (including any necessary parent directories) within
    the agent's sandboxed workspace.

    Args:
        workspace_id: The unique ID of the current agent workspace.
        relative_path: The path of the directory to create, relative to the workspace root.

    Returns:
        True if the directory was created or already existed.

    Raises:
        ValueError: If workspace_id or relative_path are invalid.
        SandboxViolationError: If the path attempts to go outside the workspace.
        IOError: If there's an error creating the directory.
    """
    logger.info(f"Attempting to create directory '{relative_path}' in workspace '{workspace_id}'")
    try:
        # Resolve and validate the path *where the directory should be created*
        # We use ensure_parent_exists=True to create the parent structure safely.
        # The final component (the directory itself) will be created by mkdir.
        absolute_path = resolve_and_validate_path(
            config=config,
            workspace_id=workspace_id,
            relative_path=relative_path,
            ensure_parent_exists=False # Let mkdir handle the final component creation
        )

        # Create the directory (and parents if necessary)
        # exist_ok=True means it won't raise an error if the directory already exists
        absolute_path.mkdir(parents=True, exist_ok=True)

        # Final check to ensure it's actually a directory now
        if not absolute_path.is_dir():
             raise IOError(f"Failed to create directory or path is not a directory: {absolute_path}")

        logger.info(f"Successfully ensured directory exists: {absolute_path}")
        return True

    except (ValueError, SandboxViolationError) as sec_err:
        logger.error(f"Security error creating directory: {sec_err}")
        raise
    except IOError as io_err:
        logger.error(f"IO error creating directory {relative_path} in {workspace_id}: {io_err}")
        raise IOError(f"Failed to create directory: {io_err}")
    except Exception as e:
        logger.exception(f"Unexpected error creating directory {relative_path} in {workspace_id}: {e}")
        raise