import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logging(level: int = logging.INFO, log_dir: str = "logs") -> None:
    # Resolve absolute path relative to mlops root
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # loggings/
    MLOPS_ROOT = os.path.dirname(BASE_DIR)                  # mlops/

    if not os.path.isabs(log_dir):
        log_dir = os.path.join(MLOPS_ROOT, log_dir)

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "mlops.log")

    handlers = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3),
    ]

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,  # VERY IMPORTANT for notebooks
    )
