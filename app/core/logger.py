import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger():
    """
    Configure application logging.
    
    Creates a logger that logs to both console and file with appropriate formatting.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Log format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # File handler (rotating to keep logs manageable)
    file_handler = RotatingFileHandler(
        "logs/knowledge_graph.log",
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set more restrictive log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Return the configured logger
    return root_logger

# Create module-level logger
logger = setup_logger()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
