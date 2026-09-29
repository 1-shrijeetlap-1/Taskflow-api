import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://taskflow:taskflow@localhost:5432/taskflow"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()

# --- PostgreSQL setup ---
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session per request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Redis setup ---
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_redis():
    return redis_client
