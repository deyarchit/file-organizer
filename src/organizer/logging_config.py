import logging.config
import sys


def setup_logger(log_level="INFO"):
    """
    Sets up the logging configuration for the entire application.
    """

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
            "detailed": {
                "format": "%(asctime)s - %(name)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s"
            },
            "compact": {"format": "%(levelname)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": log_level,
                "stream": sys.stdout,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger(__name__).info(f"Logging configured with base level: {log_level}")
