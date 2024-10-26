from typing import Optional
import aiohttp
from auth.dto import UserCreate
from auth.exceptions import MerchantCreationFailed
from loguru import logger
import os


class MerchantApiClient:
    def __init__(self, session: aiohttp.ClientSession, config: Optional[dict] = None):
        self.session = session
        self.service_url = os.getenv("USER_SERVICE_URL")
        if self.service_url is None:
            raise ValueError("USER_SERVICE_URL is not set")

        self.prefix = "/merchant"
        self.base_url = f"{self.service_url}{self.prefix}"

    async def _get_merchant(self, username: str) -> Optional[dict]:
        try:
            async with self.session.get(
                f"{self.base_url}/get_merchant?username={username}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data
                elif resp.status == 404:
                    return None
                else:
                    msg = f"Merchant {username} not found"
                    logger.info(msg)
                    return None

        except aiohttp.ClientConnectionError:
            msg = "Failed to connect to user service"
            logger.error(msg)
            raise MerchantCreationFailed(msg)
        except Exception as e:
            msg = f"Unhandled exception: {e}"
            logger.error(msg)
            raise Exception(msg)
        
        return None

    async def get_merchant_id(self, username: str) -> Optional[int]:
        merchant = await self._get_merchant(username)
        if merchant is not None:
            return merchant["id"]

        return None

    async def _create_merchant(self, merchant_registration_info: UserCreate) -> Optional[str]:
        try:
            async with self.session.post(
                f"{self.base_url}/create", json=merchant_registration_info.model_dump()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return str(data["id"])
                else:
                    msg = "Failed to create merchant"
                    logger.error(msg)
                    raise MerchantCreationFailed(msg)

        except aiohttp.ClientConnectionError:
            msg = "Failed to connect to user service"
            logger.error(msg)
            raise MerchantCreationFailed(msg)
        except Exception as e:
            msg = f"Unhandled exception: {e}"
            logger.error(msg)
            raise Exception(msg)

        return None
    async def create_merchant(self, merchant_registration_info: UserCreate) -> Optional[str]:
        return await self._create_merchant(merchant_registration_info)
