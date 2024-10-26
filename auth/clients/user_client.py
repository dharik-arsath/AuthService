import os
from typing import Optional

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field

from auth.dto import UserCreate
from auth.exceptions import UserCreationFailed


class UserGetInfo(BaseModel):
    id: int
    username: str
    is_active: bool
    full_name: str
    phone_number: str = Field(min_length=10, max_length=10, pattern="[0-9]{10}")


class UserApiClient:
    def __init__(self, session: aiohttp.ClientSession, config: Optional[dict] = None):
        self.session = session
        self.service_url = os.getenv("USER_SERVICE_URL")
        if self.service_url is None:
            raise ValueError("USER_SERVICE_URL is not set")

        self.prefix = os.getenv("USER_SERVICE_PREFIX")
        # self.prefix = None

        if self.prefix is None:
            # raise ValueError("USER_SERVICE_PREFIX not set in environment")
            self.base_url = f"{self.service_url}"
        else:
            self.base_url = f"{self.service_url}{self.prefix}"

        print(self.base_url)

    async def _get_user(self, username: str) -> Optional[UserGetInfo]:
        try:
            async with self.session.get(
                f"{self.base_url}/get_user?username={username}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        print(data)
                        return UserGetInfo(**data)
                elif resp.status == 404:
                    return None
                else:
                    msg = f"User {username} not found"
                    logger.error(msg)
                    return None

        except aiohttp.ClientConnectionError:
            msg = "Failed to connect to user service"
            logger.error(msg)
            raise UserCreationFailed(msg)
        except Exception as e:
            msg = f"Unhandled exception: {e}"
            logger.error(msg)
            raise Exception(msg)

        return None

    async def get_user_id(self, username: str) -> Optional[str]:
        user = await self._get_user(username)
        if user is not None:
            return user.id

        return None

    async def create_user(self, user_registration_info: UserCreate) -> Optional[str]:
        try:
            async with self.session.get("http://api_user:80/user/health") as response:
                print(response)
        except Exception as e:
            print(e)

        try:
            async with self.session.post(
                f"{self.base_url}/create", json=user_registration_info.model_dump()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return str(data["id"])
                else:
                    msg = "Failed to create user"
                    logger.error(msg)
                    raise UserCreationFailed(msg)

        except aiohttp.ClientConnectionError:
            msg = "Failed to connect to user service"
            logger.error(msg)
            raise UserCreationFailed(msg)
        except Exception as e:
            msg = f"Unhandled exception: {e}"
            logger.error(msg)
            raise Exception(msg)

        return None
