# mcp_server/core/security.py
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_server.config import Settings  # Assuming config loading setup

class SandboxViolationError(PermissionError):
    """Custom exception for attempts to access paths outside the sandbox."""
    pass

def resolve_and_validate_path(
    config: "Settings", # Pass your loaded config object here
    workspace_id: str,
    relative_path: str,
    ensure_parent_exists: bool = False,
    check_existence: bool = False, # Set to True if the path itself must exist
) -> Path:
    """
    Resolves a relative path within a specific workspace inside the main sandbox
    and validates that it does not escape the sandbox boundaries.

    Args:
        config: The loaded server configuration containing DIRECTORY_SANDBOX.
        workspace_id: The unique identifier for the agent's current task workspace.
        relative_path: The path provided by the agent, relative to the workspace root.
        ensure_parent_exists: If True, create the parent directories if they don't exist.
        check_existence: If True, raises an error if the final resolved path doesn't exist.

    Returns:
        The resolved, validated absolute Path object.

    Raises:
        ValueError: If workspace_id or relative_path are invalid or empty.
        SandboxViolationError: If the resolved path is outside the designated sandbox.
        FileNotFoundError: If check_existence is True and the path does not exist.
    """
    if not workspace_id:
        raise ValueError("Workspace ID cannot be empty.")
    if not relative_path:
        raise ValueError("Relative path cannot be empty.")
    if not config.DIRECTORY_SANDBOX:
         raise ValueError("DIRECTORY_SANDBOX is not configured.")

    # Basic check for directory traversal attempts in relative path input
    # normpath helps normalize separators and collapses '..' where possible upfront
    normalized_relative_path = os.path.normpath(relative_path)
    if normalized_relative_path.startswith("..") or "/../" in normalized_relative_path or "\\..\\" in normalized_relative_path:
         raise SandboxViolationError(f"Invalid relative path contains '..': {relative_path}")

    sandbox_root = Path(config.DIRECTORY_SANDBOX).resolve()
    workspace_root = (sandbox_root / workspace_id).resolve()
    target_path = (workspace_root / normalized_relative_path).resolve()

    # --- Crucial Security Check ---
    # Ensure the resolved workspace_root is within the sandbox_root
    if not str(workspace_root).startswith(str(sandbox_root)):
        raise SandboxViolationError(f"Workspace directory '{workspace_id}' is outside the sandbox '{sandbox_root}'.")

    # Ensure the final resolved target_path is still within the specific workspace_root
    # (This is the primary defense against path traversal)
    if not str(target_path).startswith(str(workspace_root)):
        raise SandboxViolationError(f"Path traversal attempt detected. Resolved path '{target_path}' is outside the workspace '{workspace_root}'.")

    # Optional: Ensure parent directories exist if writing a file
    if ensure_parent_exists:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Re-validate after potential mkdir to be absolutely sure
        if not str(target_path.parent).startswith(str(workspace_root)):
             raise SandboxViolationError("Parent directory creation resulted in path outside workspace.")


    # Optional: Check if the file/directory itself should exist
    if check_existence and not target_path.exists():
        raise FileNotFoundError(f"Required path does not exist: {target_path}")

    return target_path
