"""Logging handler for KatzenSuchApp."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from classes.Cconfig import Config

config = Config()
log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("KatzenSuchApp")

# Prevent adding handlers multiple times
if not logger.handlers:
    logger.setLevel(getattr(logging, config.log_level))
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(
        log_dir / "katzensuchapp.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_logger(name):
    return logging.getLogger(name)
