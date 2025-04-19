# starship-bridge-mcp-agent/mcp_server/tools/workspace.py
import logging
import uuid
from pathlib import Path
import shutil # For potential future cleanup tool (delete_workspace)
import re # For sanitizing project name

# Assuming access to bridge_mcp_server and config from main.py
# Adjust import if your structure differs or uses dependency injection later
from mcp_server.main import bridge_mcp_server, config
from mcp_server.core.security import resolve_and_validate_path, SandboxViolationError

logger = logging.getLogger(__name__)

@bridge_mcp_server.tool()
def create_workspace(project_name: str) -> dict:
    """
    Creates a unique, sandboxed workspace directory for a new project or task
    within the main DIRECTORY_SANDBOX.

    Args:
        project_name: A descriptive name for the project/task (used to generate workspace ID).
                      Should be relatively short and descriptive.

    Returns:
        A dictionary containing:
        - success (bool): True if the workspace was created successfully.
        - workspace_id (str | None): The unique ID (directory name) of the created workspace,
                                     or None if creation failed. This ID should be used in
                                     subsequent tool calls targeting this workspace.
        - absolute_path (str | None): The absolute server-side path to the created workspace,
                                      or None if creation failed. (Mainly for server logs).
        - error (str | None): An error message if creation failed, otherwise None.
    """
    workspace_id = None # Initialize
    try:
        if not project_name or not isinstance(project_name, str):
            raise ValueError("A valid, non-empty 'project_name' string is required.")

        # Sanitize project name for use in directory path (limit length, alphanumeric/underscore)
        # Remove leading/trailing whitespace and replace non-alphanumeric with underscore
        safe_name = re.sub(r'[^\w-]+', '_', project_name.strip())
        safe_name = safe_name[:50] # Limit length

        # Generate a unique workspace ID
        workspace_id = f"ws_{safe_name}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Attempting to create workspace with generated ID: {workspace_id} for project '{project_name}'")

        # Use resolve_and_validate_path to get the intended absolute path AND validate it's
        # within the main sandbox root *before* attempting creation.
        # We pass workspace_id as the 'workspace_id' argument and '.' as the relative path
        # to validate the root of the workspace itself.
        workspace_path = resolve_and_validate_path(
            config=config,
            workspace_id=workspace_id, # Use the generated ID here
            relative_path=".", # Target is the root of the new workspace directory
            ensure_parent_exists=False, # mkdir will create the final dir component
            check_existence=False # It should *not* exist yet
        )

        # Create the directory using pathlib
        # parents=True: Creates parent directories if needed (though sandbox root should exist)
        # exist_ok=False: Crucially, raises FileExistsError if the directory already exists
        workspace_path.mkdir(parents=True, exist_ok=False)

        logger.info(f"Successfully created workspace: {workspace_path}")
        return {
            "success": True,
            "workspace_id": workspace_id,
            "absolute_path": str(workspace_path),
            "error": None
        }

    except FileExistsError:
         # This should be extremely rare due to the UUID, but handle it defensively.
         err_msg = f"Workspace creation conflict. Directory '{workspace_id}' already exists."
         logger.error(err_msg)
         return {"success": False, "workspace_id": workspace_id, "absolute_path": None, "error": err_msg}
    except (ValueError, SandboxViolationError) as sec_err:
        # Handle validation errors (bad input, path traversal attempt)
        err_msg = f"Security or value error creating workspace for '{project_name}': {sec_err}"
        logger.error(err_msg)
        # Return None for workspace_id as it wasn't successfully created/validated
        return {"success": False, "workspace_id": None, "absolute_path": None, "error": str(sec_err)}
    except OSError as os_err:
        # Handle other OS-level errors during directory creation (e.g., permissions)
        err_msg = f"OS error creating workspace directory '{workspace_id}': {os_err}"
        logger.error(err_msg)
        return {"success": False, "workspace_id": workspace_id, "absolute_path": None, "error": err_msg}
    except Exception as e:
        # Catch any other unexpected errors
        err_msg = f"Unexpected error creating workspace for '{project_name}': {e}"
        logger.exception(err_msg) # Log full traceback for unexpected errors
        return {"success": False, "workspace_id": workspace_id, "absolute_path": None, "error": err_msg}

# --- Planned Future Tools ---
# @bridge_mcp_server.tool()
# def delete_workspace(workspace_id: str) -> dict:
#     """
#     Deletes an existing workspace directory and its contents. Use with caution.
#     Args:
#         workspace_id: The unique ID of the workspace to delete.
#     Returns:
#         A dictionary with success status and error message.
#     """
#     logger.warning(f"Attempting to delete workspace: {workspace_id}")
#     try:
#         # CRITICAL: Validate the path *before* deleting
#         workspace_path = resolve_and_validate_path(
#             config=config,
#             workspace_id=workspace_id,
#             relative_path=".",
#             check_existence=True # Ensure it exists before trying to delete
#         )
#         # Double check it's actually a directory?
#         if not workspace_path.is_dir():
#              raise NotADirectoryError(f"Path '{workspace_path}' is not a directory.")

#         # Use shutil.rmtree for recursive deletion
#         shutil.rmtree(workspace_path)
#         logger.info(f"Successfully deleted workspace: {workspace_path}")
#         return {"success": True, "error": None}

#     except (ValueError, SandboxViolationError, FileNotFoundError, NotADirectoryError) as err:
#          err_msg = f"Error deleting workspace '{workspace_id}': {err}"
#          logger.error(err_msg)
#          return {"success": False, "error": err_msg}
#     except Exception as e:
#          err_msg = f"Unexpected error deleting workspace '{workspace_id}': {e}"
#          logger.exception(err_msg)
#          return {"success": False, "error": err_msg}