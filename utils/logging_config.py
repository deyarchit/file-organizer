import logging.config
import sys


def setup_logging(log_level="INFO"):
    """
    Sets up the logging configuration for the entire application.
    """

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,
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
        "loggers": {
            "root": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger(__name__).info(f"Logging configured with base level: {log_level}")
