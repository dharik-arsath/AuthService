from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import bcrypt
import jwt  # Changed from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.clients.user_client import UserApiClient
from auth.dao.simple_password_auth_dao import SimplePasswordAuthDAO
from auth.dto import AuthCredentials, UserCreate, UserPrivate
from auth.exceptions import UserCreationFailed
from auth.utils.token_utils import get_token, set_token

# from auth.models import Au

if TYPE_CHECKING:
    from auth.models import AuthModel

    RedisType = Redis[str]  # this is only processed by mypy
else:
    RedisType = Redis  # this is not seen by mypy but will be executed at runtime


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt with a generated salt."""
    salt = bcrypt.gensalt()  # Generate a new salt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)  # Hash the password
    return hashed_password.decode("utf-8")  # Convert to string for storage


# These should be stored securely, preferably as environment variables
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int
    role: list[str]
    username: Optional[str] = None


class OAuthPasswordAuthService:
    def __init__(
        self,
        session: AsyncSession,
        auth_dao: SimplePasswordAuthDAO,
        user_client: UserApiClient,
        redis: RedisType,
    ):
        self.user_client = user_client
        self.auth_dao = auth_dao
        self.session = session

        self.redis = redis

    # async def create_access_token(
    #     self, data: dict[str, str], expires_delta: Optional[timedelta] = None
    # ) -> str:
    #     to_encode = data.copy()
    #     if expires_delta:
    #         expire = datetime.utcnow() + expires_delta
    #     else:
    #         expire = datetime.utcnow() + timedelta(minutes=15)
    #     to_encode.update({"exp": expire})
    #     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    #     return encoded_jwt

    # from datetime import datetime, timedelta, timezone

    async def create_access_token(
        self, data: dict[str, object], expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update(exp={"exp": str( expire )})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str = Depends(oauth2_scheme)) -> TokenData:
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
            stored_token = await get_token(self.redis, str(user_id))
            if stored_token is None:
                raise credentials_exception

            if str(stored_token) != token:
                raise credentials_exception

            token_data = TokenData(
                username=payload.get("sub"), user_id=user_id, role=payload.get("role")
            )
        except jwt.PyJWTError:
            raise credentials_exception
        return token_data

    async def authenticate(
        self, auth_info: AuthCredentials
    ) -> Optional[dict[str, object]]:
        user_id = await self.user_client.get_user_id(auth_info.username)

        if user_id is None:
            logger.info("User does not exist")
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="User does not exist..."
            )

        auth = await self.auth_dao.authenticate(
            str(user_id), auth_info.password.get_secret_value()
        )
        if auth:
            logger.info("User authenticated successfully, Generating token")
            logger.info("Token generated")

            return {"sub": auth_info.username, "user_id": user_id}
        else:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
            )

    async def login_for_access_token(
        self, auth_info: AuthCredentials, role: list[str]
    ) -> dict[str, str]:
        user = await self.authenticate(auth_info)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        logger.info("Creating Access Token")
        access_token = await self.create_access_token(
            data={"sub": user["sub"], "user_id": user["user_id"], "role": role},
            expires_delta=access_token_expires,
        )
        logger.info("Storing Token in Redis")

        # Store token in Redis
        # await self.store_token_in_redis(user["user_id"], access_token, access_token_expires)
        await set_token(
            self.redis, str(user["user_id"]), access_token, access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    async def create_user(self, user_registration_info: UserPrivate) -> "AuthModel":
        user_id = await self.user_client.create_user(
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
    ) -> None:
        # Convert timedelta to seconds
        expires = int(expires_delta.total_seconds())
        await self.redis.set(f"access_token:{user_id}", access_token, ex=expires)
