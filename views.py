from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

import aiohttp
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException

# add file handler for View layer
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from redis.asyncio import Redis

# from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.clients import UserApiClient
from auth.dao import SimplePasswordAuthDAO
from auth.dto import AuthCredentials, UserPrivate
from auth.services import OAuthPasswordAuthService
from auth.utils.token_utils import get_token
from database import get_db

logger.add("views.log")

if TYPE_CHECKING:
    RedisType = Redis[str]  # this is only processed by mypy
else:
    RedisType = Redis  # this is not seen by mypy but will be executed at runtime


async def get_aio_session(request: Request) -> aiohttp.ClientSession:
    if (
        hasattr(request.app.state, "aio_session")
        and type(request.app.state.aio_session) is aiohttp.ClientSession
    ):
        return request.app.state.aio_session
    else:
        logger.error("failed to get attribute aio_session")
        logger.error("AIO session not created")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def get_redis() -> RedisType:
    # redis_client = aioredis.from_url(url="redis://redis", decode_responses=True)
    redis_client = Redis.from_url(url="redis://redis", decode_responses=True)
    return redis_client


async def getUserClient(
    session: aiohttp.ClientSession = Depends(get_aio_session),
) -> UserApiClient:
    return UserApiClient(session=session)


async def getAuthService(
    session: AsyncSession = Depends(get_db),
    userClient: UserApiClient = Depends(getUserClient),
    redis: RedisType = Depends(get_redis),
) -> OAuthPasswordAuthService:
    auth_dao = SimplePasswordAuthDAO(session=session)
    return OAuthPasswordAuthService(
        session, auth_dao=auth_dao, user_client=userClient, redis=redis
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from sqlmodel import SQLModel

    from database import engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    app.state.redis = await get_redis()
    app.state.aio_session = aiohttp.ClientSession()

    logger.info("lifespan started")
    logger.info(app.state.aio_session)
    yield

    await app.state.redis.close()
    await app.state.aio_session.close()


app = FastAPI(root_path="/auth", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.on_event("startup")
# async def init_tables():
#     from sqlmodel import SQLModel

#     from database import engine

#     async with engine.begin() as conn:
#         # await conn.run_sync(SQLModel.metadata.drop_all)
#         await conn.run_sync(SQLModel.metadata.create_all)

#     app.state.redis = await get_redis()
#     app.state.aio_session = aiohttp.ClientSession()


# @app.on_event("shutdown")
# async def shutdown():
#     await app.state.redis.close()
#     await app.state.aio_session.close()


@app.post("/signin")
async def login(
    request: Request,
    auth_info: AuthCredentials,
    authService: OAuthPasswordAuthService = Depends(getAuthService),
) -> dict[str, str]:
    try:
        token_info = await authService.login_for_access_token(auth_info, role=["user"])
    except HTTPException as e:
        logger.error(f"Error while authenticating user: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error while authenticating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return token_info


@app.post("/token/verify")
async def token_verify(request: Request) -> dict[str, object]:
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
        )
    # split bearer
    token = token.split("Bearer ")[1]

    token_info = await get_token(redis_instance=app.state.redis, token=token)
    logger.info(f"token {token} info: {token_info}")

    if token_info:
        return token_info

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )


@app.post("/signup")
async def create_auth_user(
    auth_info: UserPrivate,
    authService: OAuthPasswordAuthService = Depends(getAuthService),
) -> dict[str, str]:
    try:
        auth = await authService.create_user(auth_info)
        if auth:
            return {"message": "User created successfully"}
    except HTTPException as e:
        logger.error("Error while creating user: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error while creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"health": "Good"}
