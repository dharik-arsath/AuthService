from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import time


class Base(DeclarativeBase):
    pass


HOST = "localhost"

attempt = 1
while attempt < 3:
    try:
        engine = create_async_engine(
            url=f"mysql+aiomysql://arsath:213121Ad@{HOST}/auth",
            pool_size=20,
            max_overflow=0,
            echo=True,
        )
    except Exception as e:
        print(e)

    attempt += 1
    time.sleep(3)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def get_db():
    async with SessionLocal() as db:
        yield db


# # Sync engine for DDL operations (like table creation)
# sync_engine = create_engine("mysql+aiomysql://arsath:213121Ad@localhost/user")
