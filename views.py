from fastapi import FastAPI, Depends
from auth.services import SimplePasswordAuthService
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth.dao import SimplePasswordAuthDAO
from auth.dto import UserAuthData, AuthCredentials
from fastapi.exceptions import HTTPException
from auth.clients import UserApiClient

from loguru import logger

# add file handler for View layer

logger.add("views.log")


async def getUserClient() -> UserApiClient:
    return UserApiClient()


async def getAuthService(
    session: AsyncSession = Depends(get_db),
    userClient: UserApiClient = Depends(getUserClient),
) -> SimplePasswordAuthService:
    auth_dao = SimplePasswordAuthDAO(session=session)
    return SimplePasswordAuthService(session, authDAO=auth_dao, user_client=userClient)


app = FastAPI()


@app.post("/login")
async def login(
    auth_info: AuthCredentials,
    authService: SimplePasswordAuthService = Depends(getAuthService),
):
    token = await authService.authenticate(auth_info)
    if token is None:
        logger.info("Invalid username or password")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return token


@app.post("/create_auth_user")
async def create_auth_user(
    auth_info: UserAuthData,
    authService: SimplePasswordAuthService = Depends(getAuthService),
):
    auth = await authService.create_auth_user(auth_info)

    return auth
