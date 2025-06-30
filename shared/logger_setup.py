# # # shared/logger_setup.py
# # import logging
# # import sys
# # import os
# # from logging.handlers import RotatingFileHandler
# #
# #
# # def setup_logging():
# #     log_level = os.getenv("LOG_LEVEL", "INFO").upper()
# #     logger = logging.getLogger("WebsiteMonitorBot")
# #     logger.setLevel(log_level)
# #     handler = RotatingFileHandler("app.log", maxBytes=10 * 1024 * 1024, backupCount=5)
# #     handler.setFormatter(
# #         logging.Formatter(
# #             "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
# #         )
# #     )
# #     logger.addHandler(handler)
# #     console_handler = logging.StreamHandler(sys.stdout)
# #     console_handler.setFormatter(
# #         logging.Formatter(
# #             "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
# #         )
# #     )
# #     logger.addHandler(console_handler)
# #     logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
# #     logging.getLogger("celery").setLevel(logging.INFO)
# #     logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
# #     logging.getLogger("aiogram.client.session").setLevel(logging.WARNING)
# #     logging.getLogger("asyncio").setLevel(logging.WARNING)
# #     return logger
# #
# #
# # logger = setup_logging()
# import logging
# import sys
# import os
# from logging.handlers import RotatingFileHandler
#
#
# def setup_logging():
#     log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
#     logger = logging.getLogger("WebsiteMonitorBot")
#     logger.setLevel(log_level)
#
#     # Формат логов, аналогичный примеру
#     log_format = logging.Formatter(
#         "%(asctime)s | %(levelname)s | [%(filename)s:%(lineno)d] - %(message)s",
#         "%Y-%m-%d %H:%M:%S",
#     )
#     os.makedirs("logs", exist_ok=True)
#     # Логи в файл с ротацией
#     file_handler = RotatingFileHandler(
#         "logs/bot_errors.log",
#         maxBytes=10 * 1024 * 1024,
#         backupCount=5,
#         encoding="utf-8",
#     )
#     file_handler.setLevel(logging.ERROR)  # Только ошибки в файл
#     file_handler.setFormatter(log_format)
#     logger.addHandler(file_handler)
#
#     # Логи в консоль
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setLevel(log_level)
#     console_handler.setFormatter(log_format)
#     logger.addHandler(console_handler)
#
#     # Настройка сторонних логгеров
#     logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
#     logging.getLogger("celery").setLevel(logging.INFO)
#     logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
#     logging.getLogger("aiogram.client.session").setLevel(logging.WARNING)
#     logging.getLogger("asyncio").setLevel(logging.WARNING)
#
#     return logger
#
#
# logger = setup_logging()
# Без изменений, сохранена структура
import logging
from logging.handlers import RotatingFileHandler
import sys
import os


def setup_logging():
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logger = logging.getLogger("WebsiteMonitorBot")
    logger.setLevel(log_level)
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = RotatingFileHandler("bot.log", maxBytes=10_000_000, backupCount=5)
    file_handler.setFormatter(log_format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
