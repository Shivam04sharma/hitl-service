"""Human-in-the-Loop (HITL) Service."""

import asyncio
import socket
from contextlib import asynccontextmanager

import structlog
import uvicorn
from config import settings
from db.session import close_db, get_session, init_db
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from routes.reviews import router as reviews_router
from routes.chat import router as chat_router
from services import review_store

logger = structlog.get_logger()


async def expire_events_task():
    """Background task to expire old shown events."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            async for db in get_session():
                count = await review_store.expire_old_events(
                    db, settings.review_default_sla_seconds
                )
                if count > 0:
                    logger.info("expired_events", count=count)
        except Exception as exc:
            logger.error("expire_task_error", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("startup", service=settings.service_name, env=settings.env, port=settings.port)
    
    # Start background expiry task
    task = asyncio.create_task(expire_events_task())
    
    yield
    
    # Cancel background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    await close_db()
    logger.info("shutdown", service=settings.service_name)


app = FastAPI(
    title="HITL — Human-in-the-Loop",
    version="1.0.0",
    description="Human-in-the-Loop decision service for AI chat systems.",
    lifespan=lifespan,
    root_path="/hitl",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import RedirectResponse


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
    )


# UI routes - excluded from schema
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/chat.html")

@app.get("/dashboard", include_in_schema=False)
async def dashboard_page():
    return RedirectResponse(url="/static/dashboard.html")

# Mount static files AFTER defining routes
app.mount("/static", StaticFiles(directory="src/static"), name="static")


app.include_router(reviews_router, prefix="/api/v1", tags=["hitl"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])


@app.get("/health", tags=["health"])
@app.get("/actuator/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": app.version,
        "env": settings.env,
        "app_instance": socket.gethostname(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
