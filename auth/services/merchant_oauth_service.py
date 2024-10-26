from datetime import datetime, timedelta
from typing import Optional

import aioredis
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.clients.merchant_client import MerchantApiClient
from auth.dao.simple_password_auth_dao import SimplePasswordAuthDAO
from auth.dto import AuthCredentials, UserCreate, UserPrivate
from auth.exceptions import UserCreationFailed
from auth.utils.security import hash_password
from auth.utils.token_utils import get_token, set_token

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    username: str | None = None
    user_id: int
    role: list[str]


class MerchantOAuthPasswordAuthService:
    def __init__(
        self,
        session: AsyncSession,
        auth_dao: SimplePasswordAuthDAO,
        merchant_client: MerchantApiClient,
        redis: aioredis.Redis,
    ):
        self.merchant_client = merchant_client
        self.auth_dao = auth_dao
        self.session = session
        self.redis = redis

    async def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: Optional[int] = payload.get("user_id")
            if user_id is None:
                raise credentials_exception

            # Verify token in Redis
            stored_token = await get_token(self.redis, user_id)
            if stored_token != token:
                raise credentials_exception

            token_data = TokenData(
                username=payload.get("sub"), user_id=user_id, role=payload.get("role")
            )
        except jwt.PyJWTError:
            raise credentials_exception
        return token_data

    async def authenticate(self, auth_info: AuthCredentials):
        user_id = await self.merchant_client.get_merchant_id(auth_info.username)
        if user_id is None:
            logger.info("User does not exist")
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="User does not exist..."
            )

        auth = await self.auth_dao.authenticate(
            user_id, auth_info.password.get_secret_value()
        )
        if auth:
            logger.info("User authenticated successfully, Generating token")
            logger.info("Token generated")

            return {"sub": auth_info.username, "user_id": user_id}
        else:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
            )

    async def login_for_access_token(self, auth_info: AuthCredentials, role: list[str]):
        user = await self.authenticate(auth_info)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await self.create_access_token(
            data={"sub": user["sub"], "user_id": user["user_id"], "role": role},
            expires_delta=access_token_expires,
        )

        # Store token in Redis
        # await self.store_token_in_redis(user["user_id"], access_token, access_token_expires)
        await set_token(self.redis, user["user_id"], access_token, access_token_expires)

        return {"access_token": access_token, "token_type": "bearer"}

    async def create_user(self, user_registration_info: UserPrivate):
        user_id = await self.merchant_client.create_merchant(
            UserCreate(**user_registration_info.model_dump())
        )
        if user_id is None:
            logger.info(
                f"User creation failed for user {user_registration_info.username}"
            )
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User creation failed")

        logger.info("User created successfully on User Model")

        password = hash_password(user_registration_info.password.get_secret_value())

        try:
            auth = await self.auth_dao.create_user(user_id, password)
            await self.session.commit()
            await self.session.refresh(auth)
        except UserCreationFailed as e:
            logger.error(e)
            await self.session.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="User already exists")

        logger.info("User created successfully on Auth Model")

        return auth

    async def store_token_in_redis(
        self, user_id: int, access_token: str, expires_delta: timedelta
    ):
        # Convert timedelta to seconds
        expires = int(expires_delta.total_seconds())
        await self.redis.set(f"access_token:{user_id}", access_token, ex=expires)
