import os
import time
from typing import AsyncGenerator

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Engine(BaseModel):
    engine: AsyncEngine | None = Field(default=None)

    class Config:
        arbitrary_types_allowed = True


engine_cfg = Engine()


class Base(DeclarativeBase):
    pass


HOST = os.environ.get("MYSQL_HOST", "localhost")
PORT = os.environ.get("MYSQL_PORT", 3308)
DATABASE = os.environ.get("MYSQL_DATABASE", "auth")
DATABASE_URL = os.environ.get("DATABASE_URL")

attempt = 1
while attempt < 10:
    try:
        engine = create_async_engine(
            url=str(DATABASE_URL),
            pool_size=20,
            max_overflow=0,
            echo=True,
        )
        engine_cfg.engine = engine

    except Exception as e:
        print(e)

    if engine_cfg.engine is not None:
        break

    print("Cannot connect to database. Retrying in 3 seconds...")
    attempt += 1
    time.sleep(3)

assert engine_cfg.engine is not None, "Cannot connect to database"

SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine_cfg.engine, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db


async def get_engine() -> AsyncEngine:
    if engine_cfg.engine is None:
        raise Exception("Engine not initialized")

    return engine_cfg.engine
