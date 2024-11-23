import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..config import get_env_var

DEFAULT_LOG_LEVEL = "INFO"

def setup_logging(
    log_file: Optional[Path] = None,
    module: str = "git_stalker"
) -> logging.Logger:
    """Configure logging with console and optional file handlers."""
    
    # Get log level from environment
    level = get_env_var("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    
    # Create logger
    logger = logging.getLogger(module)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logging() 