"""
logger.py
---------

Central logging configuration for the ETL Pipeline.

Features
--------
- Console logging
- File logging
- Standard log format
- Singleton logger (avoids duplicate handlers)
"""

import logging
from pathlib import Path

from etl.config import LOG_FILE


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a configured logger.

    Parameters
    ----------
    name : str
        Logger name (usually __name__ or class name)

    Returns
    -------
    logging.Logger
    """

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ------------------------------------------------------
    # File Handler
    # ------------------------------------------------------

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # ------------------------------------------------------
    # Console Handler
    # ------------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ------------------------------------------------------
    # Register Handlers
    # ------------------------------------------------------

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger