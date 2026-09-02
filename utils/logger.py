"""
Centralized logging setup.

Every module calls get_logger(__name__) to get a logger that writes to
both the console and a rotating-free log file, using a consistent format.
"""

import logging

from config import LOG_LEVEL, LOG_FILE


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger, reusing handlers if already set up."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        # If the filesystem is read-only or the path is invalid, fall back
        # to console-only logging and emit a warning so problems are visible.
        logger.warning(
            "Failed to create log file handler '%s'; continuing with console-only logging: %s",
            LOG_FILE,
            exc,
        )

    return logger
