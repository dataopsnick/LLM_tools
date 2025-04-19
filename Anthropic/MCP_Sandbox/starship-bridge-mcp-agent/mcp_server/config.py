# mcp_server/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    """Server configuration loaded from .env file."""
    # Use model_config for Pydantic v2 settings
    model_config = SettingsConfigDict(
        # Load from .env file in the directory specified or parent dirs
        env_file='.env',
        # Allow extra fields if needed, though define expected ones
        extra='ignore'
    )

    # Mandatory: The root directory for agent workspaces
    DIRECTORY_SANDBOX: str

    # Optional: Add other configs like AWS keys, Stripe, etc. here
    # These will be automatically loaded from the .env file if present
    GEMINI_API_KEY: str | None = None
    AWS_REGION: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_SESSION_TOKEN: str | None = None # For temporary creds
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    # Add VERCEL/COOLIFY tokens if needed

    # Add default values or leave as None if optional