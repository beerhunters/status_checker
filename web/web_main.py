from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from shared.db import init_db
from shared.logger_setup import setup_logging
from web.auth import router as auth_router
from web.routers import router as main_router
import logging
from typing import Optional
import traceback

app = FastAPI(title="Website Monitor Admin Panel")
templates = Jinja2Templates(directory="web/templates")
logger = logging.getLogger("WebsiteMonitorBot")


class ErrorInfo:
    def __init__(self, exception: Exception, request: Optional[Request] = None):
        self.exception = exception
        self.request = request
        self.traceback_info = "".join(traceback.format_tb(exception.__traceback__))

    def _get_error_location(self) -> str:
        tb = traceback.extract_tb(self.exception.__traceback__)
        last_call = tb[-1]
        filename = last_call.filename
        line = last_call.lineno
        func = last_call.name
        code_line = last_call.line.strip() if last_call.line else "???"
        return f"{filename}:{line} in {func} -> {code_line}"

    def _format_traceback(self, max_length: int = 2000) -> str:
        tb_lines = self.traceback_info.splitlines()
        snippet = "\n".join(tb_lines[-10:])
        return snippet[:max_length]


@app.on_event("startup")
async def startup_event():
    setup_logging()
    await init_db()
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    error_info = ErrorInfo(exc, request)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 404,
            "detail": "Page not found",
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: Exception):
    error_info = ErrorInfo(exc, request)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": f"Internal Server Error: {str(exc)}",
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


app.include_router(auth_router)
app.include_router(main_router)
