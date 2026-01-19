"""
Centralized logging configuration for TravelGuru v5.
Provides consistent logging setup across the entire backend.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Union


def setup_logging(
    level: Union[int, str] = "INFO",
    log_to_file: bool = False,
    log_file_path: str | None = None
) -> None:
    """
    Configure centralized logging for the application.
    
    This function is idempotent and can be called multiple times safely.
    Each call will reset the logging configuration.
    
    Args:
        level: Logging level as string ("DEBUG", "INFO", etc.) or int
        log_to_file: Whether to enable file logging in addition to console
        log_file_path: Path to log file (default: logs/travelguru.log)
    
    Examples:
        >>> setup_logging()  # INFO level, console only
        >>> setup_logging("DEBUG", log_to_file=True)  # DEBUG level, console + file
        >>> setup_logging(logging.WARNING)  # WARNING level, console only
    """
    # Convert string level to numeric if needed
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    else:
        numeric_level = level
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates (idempotency)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # Define log format
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Add console handler (always)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Use default path if not provided
        if log_file_path is None:
            log_file_path = "logs/travelguru.log"
        
        # Create directories if they don't exist
        try:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler (5MB max, 3 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # Log to console but don't crash the app
            console_handler.handle(
                logging.LogRecord(
                    name="logging_setup",
                    level=logging.WARNING,
                    pathname=__file__,
                    lineno=0,
                    msg=f"Failed to setup file logging: {e}",
                    args=(),
                    exc_info=None
                )
            )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Logger instance
        
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return logging.getLogger(name)
