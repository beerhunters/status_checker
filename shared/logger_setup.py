# shared/logger_setup.py
import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger("WebsiteMonitorBot")
    logger.setLevel(log_level)
    handler = RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(console_handler)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiogram.client.session").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    return logger


logger = setup_logging()
