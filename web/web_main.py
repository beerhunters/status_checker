# # # # web/web_main.py
# # # from fastapi import FastAPI, Request
# # # from fastapi.responses import HTMLResponse
# # # from fastapi.staticfiles import StaticFiles
# # # from fastapi.templating import Jinja2Templates
# # # from web.auth import router as auth_router
# # # from web.routers import router as sites_router
# # # from shared.db import init_db
# # # from shared.logger_setup import logger
# # #
# # # app = FastAPI(title="Website Monitor Admin Panel")
# # # templates = Jinja2Templates(directory="web/templates")
# # #
# # # app.include_router(auth_router, tags=["Authentication"])
# # # app.include_router(sites_router, tags=["Admin Panel"])
# # #
# # #
# # # @app.on_event("startup")
# # # async def startup_event():
# # #     logger.info("Starting Web Application...")
# # #     try:
# # #         await init_db()
# # #         logger.info("Database initialized successfully")
# # #     except Exception as e:
# # #         logger.critical(f"Error initializing database: {e}", exc_info=True)
# # #         raise
# # #
# # #
# # # @app.on_event("shutdown")
# # # async def shutdown_event():
# # #     logger.info("Shutting Down Web Application...")
# # #
# # #
# # # @app.exception_handler(404)
# # # async def not_found_exception_handler(request: Request, exc: Exception):
# # #     return templates.TemplateResponse(
# # #         "error.html",
# # #         {"request": request, "status_code": 404, "detail": "Страница не найдена."},
# # #         status_code=404,
# # #     )
# # #
# # #
# # # @app.exception_handler(500)
# # # async def internal_error_exception_handler(request: Request, exc: Exception):
# # #     logger.error(f"Internal server error: {exc}", exc_info=True)
# # #     return templates.TemplateResponse(
# # #         "error.html",
# # #         {
# # #             "request": request,
# # #             "status_code": 500,
# # #             "detail": "Внутренняя ошибка сервера.",
# # #         },
# # #         status_code=500,
# # #     )
# # from fastapi import FastAPI, Request
# # from fastapi.responses import HTMLResponse
# # from fastapi.templating import Jinja2Templates
# # from web.auth import router as auth_router
# # from web.routers import router as sites_router
# # from shared.db import init_db
# # from shared.logger_setup import logger
# # from datetime import datetime
# # import traceback
# # from typing import Optional
# # from fastapi import FastAPI, Request, status
# # from fastapi.responses import HTMLResponse
# # from shared.logger_setup import logger
# #
# # app = FastAPI(title="Website Monitor Admin Panel")
# # templates = Jinja2Templates(directory="web/templates")
# # app.include_router(auth_router, tags=["Authentication"])
# # app.include_router(sites_router, tags=["Admin Panel"])
# #
# #
# # class ErrorInfo:
# #     def __init__(self, exception: Exception, request: Optional[Request] = None):
# #         self.exception = exception
# #         self.exception_name = type(exception).__name__
# #         self.exception_message = str(exception)
# #         self.error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# #         self.request = request
# #         self.traceback_info = traceback.format_exc()
# #         self.traceback_snippet = self._format_traceback()
# #         self.error_location = self._get_error_location()
# #
# #     def _get_error_location(self) -> str:
# #         if not hasattr(self.exception, "__traceback__"):
# #             return "❓ Неизвестное местоположение"
# #         tb = traceback.extract_tb(self.exception.__traceback__)
# #         if not tb:
# #             return "❓ Неизвестное местоположение"
# #         last_call = tb[-1]
# #         filename = last_call.filename
# #         line = last_call.lineno
# #         func = last_call.name
# #         code_line = last_call.line.strip() if last_call.line else "???"
# #         return (
# #             f"📂 <b>Файл:</b> {filename}\n"
# #             f"📌 <b>Строка:</b> {line}\n"
# #             f"🔹 <b>Функция:</b> {func}\n"
# #             f"🖥 <b>Код:</b> <pre>{code_line}</pre>"
# #         )
# #
# #     def _format_traceback(self, max_length: int = 2000) -> str:
# #         tb_lines = self.traceback_info.splitlines()
# #         snippet = (
# #             "\n".join(tb_lines[-4:]) if len(tb_lines) >= 4 else self.traceback_info
# #         )
# #         if len(snippet) > max_length:
# #             return snippet[:max_length] + "\n...[сокращено]"
# #         return snippet
# #
# #
# # @app.on_event("startup")
# # async def startup_event():
# #     logger.info("Starting Web Application...")
# #     try:
# #         await init_db()
# #         logger.info("Database initialized successfully")
# #     except Exception as e:
# #         error_info = ErrorInfo(e)
# #         logger.error(
# #             "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
# #             error_info.exception_name,
# #             error_info.exception_message,
# #             error_info.error_location.replace("\n", " | "),
# #             error_info.traceback_snippet,
# #         )
# #         raise
# #
# #
# # @app.on_event("shutdown")
# # async def shutdown_event():
# #     logger.info("Shutting Down Web Application...")
# #
# #
# # # @app.exception_handler(404)
# # # async def not_found_exception_handler(request: Request, exc: Exception):
# # #     error_info = ErrorInfo(exc, request)
# # #     logger.error(
# # #         "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
# # #         error_info.exception_name,
# # #         error_info.exception_message,
# # #         error_info.error_location.replace("\n", " | "),
# # #         error_info.traceback_snippet,
# # #     )
# # #     return templates.TemplateResponse(
# # #         "error.html",
# # #         {"request": request, "status_code": 404, "detail": "Страница не найдена."},
# # #         status_code=404,
# # #     )
# # @app.exception_handler(404)
# # async def not_found_exception_handler(request: Request, exc: Exception):
# #     error_info = ErrorInfo(exc, request)
# #     logger.error(f"404 Error: {error_info._format_traceback()}")
# #     return templates.TemplateResponse(
# #         "error.html",
# #         {"request": request, "detail": str(exc), "status_code": 404},
# #         status_code=status.HTTP_404_NOT_FOUND,
# #     )
# #
# #
# # # @app.exception_handler(500)
# # # async def internal_error_exception_handler(request: Request, exc: Exception):
# # #     error_info = ErrorInfo(exc, request)
# # #     logger.error(
# # #         "Ошибка %s: %s\nМестоположение: %s\nTraceback: %s",
# # #         error_info.exception_name,
# # #         error_info.exception_message,
# # #         error_info.error_location.replace("\n", " | "),
# # #         error_info.traceback_snippet,
# # #     )
# # #     return templates.TemplateResponse(
# # #         "error.html",
# # #         {
# # #             "request": request,
# # #             "status_code": 500,
# # #             "detail": "Внутренняя ошибка сервера.",
# # #         },
# # #         status_code=500,
# # #     )
# # @app.exception_handler(500)
# # async def internal_error_exception_handler(request: Request, exc: Exception):
# #     error_info = ErrorInfo(exc, request)
# #     logger.error(f"500 Error: {error_info._format_traceback()}")
# #     return templates.TemplateResponse(
# #         "error.html",
# #         {"request": request, "detail": "Внутренняя ошибка сервера", "status_code": 500},
# #         status_code=status.HTTP_500_INTERNAL_SERVER,
# #     )
# # Изменения: Убраны ссылки на Celery, обновлены импорты
# from fastapi import FastAPI, Request
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# from web.routers import router as api_router
# from web.auth import router as auth_router
# from shared.db import init_db
# import traceback
# import logging
# from typing import Optional
#
# app = FastAPI(title="Website Monitor Admin Panel")
# templates = Jinja2Templates(directory="web/templates")
# logger = logging.getLogger("WebsiteMonitorBot")
#
#
# class ErrorInfo:
#     def __init__(self, exception: Exception, request: Optional[Request] = None):
#         self.exception = exception
#         self.request = request
#         self.traceback_info = traceback.format_exc()
#
#     def _get_error_location(self) -> str:
#         tb = traceback.extract_tb(self.exception.__traceback__)
#         last_call = tb[-1]
#         filename = last_call.filename
#         line = last_call.lineno
#         func = last_call.name
#         code_line = last_call.line.strip() if last_call.line else "???"
#         return f"{filename}:{line} ({func}): {code_line}"
#
#     def _format_traceback(self, max_length: int = 2000) -> str:
#         tb_lines = self.traceback_info.splitlines()
#         snippet = "\n".join(tb_lines[-10:])
#         return snippet[:max_length]
#
#
# @app.on_event("startup")
# async def startup_event():
#     try:
#         await init_db()
#     except Exception as e:
#         logger.error(f"Startup error: {str(e)}")
#
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     pass
#
#
# @app.exception_handler(404)
# async def not_found_exception_handler(request: Request, exc: Exception):
#     error_info = ErrorInfo(exc, request)
#     logger.error(f"404 error: {error_info._format_traceback()}")
#     return templates.TemplateResponse(
#         "error.html",
#         {"request": request, "status_code": 404, "detail": "Страница не найдена"},
#     )
#
#
# @app.exception_handler(500)
# async def internal_error_exception_handler(request: Request, exc: Exception):
#     error_info = ErrorInfo(exc, request)
#     logger.error(f"500 error: {error_info._format_traceback()}")
#     return templates.TemplateResponse(
#         "error.html",
#         {"request": request, "status_code": 500, "detail": "Внутренняя ошибка сервера"},
#     )
#
#
# app.include_router(api_router)
# app.include_router(auth_router)
# Изменения: Добавлена обработка ошибок в startup_event
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from web.routers import router as api_router
from web.auth import router as auth_router
from shared.db import init_db
import traceback
import logging
from typing import Optional

app = FastAPI(title="Website Monitor Admin Panel")
templates = Jinja2Templates(directory="web/templates")
logger = logging.getLogger("WebsiteMonitorBot")


class ErrorInfo:
    def __init__(self, exception: Exception, request: Optional[Request] = None):
        self.exception = exception
        self.request = request
        self.traceback_info = traceback.format_exc()

    def _get_error_location(self) -> str:
        tb = traceback.extract_tb(self.exception.__traceback__)
        last_call = tb[-1]
        filename = last_call.filename
        line = last_call.lineno
        func = last_call.name
        code_line = last_call.line.strip() if last_call.line else "???"
        return f"{filename}:{line} ({func}): {code_line}"

    def _format_traceback(self, max_length: int = 2000) -> str:
        tb_lines = self.traceback_info.splitlines()
        snippet = "\n".join(tb_lines[-10:])
        return snippet[:max_length]


@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    pass


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    error_info = ErrorInfo(exc, request)
    logger.error(f"404 error: {error_info._format_traceback()}")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 404, "detail": "Страница не найдена"},
    )


@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: Exception):
    error_info = ErrorInfo(exc, request)
    logger.error(f"500 error: {error_info._format_traceback()}")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 500, "detail": "Внутренняя ошибка сервера"},
    )


app.include_router(api_router)
app.include_router(auth_router)
