import os
from typing import Optional
from dotenv import load_dotenv

def get_github_token() -> str:
    """Get GitHub token from environment variables."""
    _ = load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token is missing. Please set it in the .env file.")
    return token

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default value."""
    _ = load_dotenv()
    return os.getenv(key, default) 