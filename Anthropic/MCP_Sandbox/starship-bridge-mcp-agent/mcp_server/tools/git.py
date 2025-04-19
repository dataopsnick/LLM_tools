# mcp_server/tools/git.py
import logging
import subprocess
from pathlib import Path
from typing import Any

# Assuming access to bridge_mcp_server and config from main.py
from mcp_server.main import bridge_mcp_server, config
from mcp_server.core.security import resolve_and_validate_path, SandboxViolationError

logger = logging.getLogger(__name__)

def _run_git_command(workspace_id: str, relative_dir: str, command_args: list[str]) -> dict[str, Any]:
    """Helper function to run git commands securely within the workspace."""
    logger.info(f"Running git command: {' '.join(command_args)} in workspace '{workspace_id}/{relative_dir}'")
    try:
        # Resolve and validate the working directory path
        working_dir_path = resolve_and_validate_path(
            config=config,
            workspace_id=workspace_id,
            relative_path=relative_dir,
            check_existence=True # Ensure the directory exists
        )
        if not working_dir_path.is_dir():
            raise NotADirectoryError(f"Git working directory is not valid: {working_dir_path}")

        # Construct the full command
        full_command = ["git"] + command_args

        # Execute the command
        # Capture output, use text mode, set cwd, check for errors
        result = subprocess.run(
            full_command,
            cwd=working_dir_path,
            capture_output=True,
            text=True,
            check=False # We check the returncode manually for better error reporting
        )

        logger.info(f"Git command finished with code: {result.returncode}")
        if result.returncode != 0:
             logger.error(f"Git command error: {result.stderr}")
        #else:
             #logger.debug(f"Git command stdout: {result.stdout}") # Optional: log success stdout

        return {
            "command": " ".join(full_command),
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "success": result.returncode == 0
        }

    except (ValueError, SandboxViolationError, FileNotFoundError, NotADirectoryError) as err:
        logger.error(f"Error preparing git command: {err}")
        return {"success": False, "stderr": str(err), "returncode": -1}
    except Exception as e:
        logger.exception(f"Unexpected error running git command {' '.join(command_args)}: {e}")
        return {"success": False, "stderr": str(e), "returncode": -1}


@bridge_mcp_server.tool()
def git_clone(workspace_id: str, repo_url: str, directory: str = ".") -> dict[str, Any]:
    """Clones a git repository into a specified directory within the workspace."""
    # Note: Cloning target directory is relative *within* the specified 'directory' arg
    # which itself is relative to the workspace. Usually directory="."
    return _run_git_command(workspace_id, directory, ["clone", repo_url, "."]) # Clone into the validated dir

@bridge_mcp_server.tool()
def git_commit(workspace_id: str, message: str, add_all: bool = True, directory: str = ".") -> dict[str, Any]:
    """Creates a git commit with the given message. Optionally stages all changes first."""
    if add_all:
        add_result = _run_git_command(workspace_id, directory, ["add", "."])
        if not add_result["success"]:
            logger.error(f"git add failed: {add_result['stderr']}")
            return add_result # Return the error from git add
    return _run_git_command(workspace_id, directory, ["commit", "-m", message])

@bridge_mcp_server.tool()
def git_diff_staged(workspace_id: str, directory: str = ".") -> dict[str, Any]:
    """Shows changes staged for the next commit."""
    return _run_git_command(workspace_id, directory, ["diff", "--staged"])

@bridge_mcp_server.tool()
def git_push(workspace_id: str, directory: str = ".", remote: str = "origin", branch: str = "main") -> dict[str, Any]:
    """Pushes commits to the specified remote and branch."""
    return _run_git_command(workspace_id, directory, ["push", remote, branch])

@bridge_mcp_server.tool()
def git_pull(workspace_id: str, directory: str = ".", remote: str = "origin", branch: str = "main") -> dict[str, Any]:
    """Pulls changes from the specified remote and branch."""
    return _run_git_command(workspace_id, directory, ["pull", remote, branch])

@bridge_mcp_server.tool()
def git_create_branch(workspace_id: str, branch_name: str, directory: str = ".") -> dict[str, Any]:
    """Creates a new git branch."""
    return _run_git_command(workspace_id, directory, ["branch", branch_name])

@bridge_mcp_server.tool()
def git_checkout_branch(workspace_id: str, branch_name: str, directory: str = ".") -> dict[str, Any]:
    """Checks out an existing git branch."""
    return _run_git_command(workspace_id, directory, ["checkout", branch_name])
