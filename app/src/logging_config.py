import logging
import logging.config


def setup_logging(default_level=logging.INFO):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "standard",
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": default_level,
                "propagate": True,
            },
            # Suppress LiteLLM logs
            "LiteLLM": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
            "LiteLLM.Router": {
                "handlers": [],
                "level": "ERROR",
                "propagate": False,
            },
            "LiteLLM.Proxy": {
                "handlers": [],
                "level": "ERROR",
                "propagate": False,
            },
            # Suppress other noisy loggers
            "httpx": {
                "handlers": [],
                "level": "WARNING",
                "propagate": False,
            },
            "httpcore": {
                "handlers": [],
                "level": "WARNING",
                "propagate": False,
            },
            # Application loggers
            "streamlit": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "agent": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "ui": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
