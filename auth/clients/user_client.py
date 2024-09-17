from typing import Optional
import aiohttp


class UserApiClient:
    def __init__(self, config: Optional[dict] = None):
        if config.get("base_url"):
            self.base_url = config.get("base_url")
        else:
            self.base_url = "http://localhost:8000/user/"

    async def _get_user(self, username: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/get_user/{username}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data

                return

    async def get_user_id(self, username: str):
        user = await self._get_user(username)
        if user is not None:
            return user["id"]

        return
