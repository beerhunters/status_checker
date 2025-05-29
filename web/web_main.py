# web/web_main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from web.auth import router as auth_router
from web.routers import router as sites_router
from shared.db import init_db
from shared.logger_setup import logger

app = FastAPI(title="Website Monitor Admin Panel")
templates = Jinja2Templates(directory="web/templates")

app.include_router(auth_router, tags=["Authentication"])
app.include_router(sites_router, tags=["Admin Panel"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Web Application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical(f"Error initializing database: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting Down Web Application...")


@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 404, "detail": "Страница не найдена."},
        status_code=404,
    )


@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": "Внутренняя ошибка сервера.",
        },
        status_code=500,
    )
