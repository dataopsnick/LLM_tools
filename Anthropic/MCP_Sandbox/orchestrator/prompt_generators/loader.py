# orchestrator/prompt_generators/loader.py
import importlib
import inspect
import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Tuple

logger = logging.getLogger("OrchestratorClient.PromptLoader")

# Type hint for the generator functions (Problem String -> Prompt String)
PromptGeneratorFunc = Callable[[str], str]
# Simpler type hint without optional args for loader:
SimplePromptGeneratorFunc = Callable[[str], str]


def load_prompt_generators(directory: str | Path = Path(__file__).parent) -> Dict[str, SimplePromptGeneratorFunc]:
    """
    Dynamically loads prompt generator functions from .py files in a directory.

    Assumes each .py file contains one primary function matching the filename
    (e.g., swot_analysis.py contains def swot_analysis(problem_statement: str) -> str).
    Adjust logic if function names differ or files contain multiple generators.

    Args:
        directory: The directory containing the .py generator files.

    Returns:
        A dictionary mapping generator names (e.g., "swot_analysis") to the callable functions.
    """
    generators: Dict[str, SimplePromptGeneratorFunc] = {}
    dir_path = Path(directory)
    logger.info(f"Loading prompt generators from: {dir_path.resolve()}")

    for filename in os.listdir(dir_path):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]  # Remove .py extension
            function_name = module_name # Assume function name matches module name
            try:
                # Construct the full module path relative to the project structure
                # This assumes 'orchestrator' is a package root or accessible via sys.path
                module_path = f"orchestrator.prompt_generators.{module_name}"
                module = importlib.import_module(module_path)

                if hasattr(module, function_name):
                    func = getattr(module, function_name)
                    # Basic check: ensure it's a callable function
                    # More robust check: inspect signature to ensure it takes one string arg
                    if callable(func):
                         # Simplified check: We assume it takes one arg for loading.
                         # Runtime call will handle type errors if signature is wrong.
                        sig = inspect.signature(func)
                        if len(sig.parameters) >= 1: # Needs at least the main problem arg
                             # Store the function directly
                             generators[function_name] = func
                             logger.debug(f"Successfully loaded generator: {function_name}")
                        else:
                             logger.warning(f"Skipping {function_name} in {filename}: Incorrect signature (needs at least one argument).")

                    else:
                        logger.warning(f"Skipping {function_name} in {filename}: Not a callable function.")
                else:
                    logger.warning(f"Skipping {filename}: Function '{function_name}' not found.")
            except ImportError as e:
                logger.error(f"Failed to import module {module_path}: {e}")
            except Exception as e:
                logger.error(f"Error loading generator from {filename}: {e}")

    logger.info(f"Loaded {len(generators)} prompt generators: {list(generators.keys())}")
    return generators