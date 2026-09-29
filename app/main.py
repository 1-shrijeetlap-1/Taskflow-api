import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import engine, Base, get_redis
from app.routers import auth, tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("taskflow")

app = FastAPI(
    title="TaskFlow API",
    description="A JWT-authenticated task management API with Redis caching.",
    version="1.0.0",
)

# Creates tables if they don't exist. For real migrations, use Alembic instead.
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/health", tags=["health"])
def health_check():
    """Used by load balancers / uptime monitors to verify the service is alive."""
    redis_ok = True
    try:
        get_redis().ping()
    except Exception:
        redis_ok = False
    return {"status": "ok", "redis": redis_ok}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
