from sqlalchemy.ext.asyncio import AsyncSession
from auth.dao import SimplePasswordAuthDAO
from auth.utils.token_utils import generate_token
from loguru import logger
from auth.clients import UserApiClient
from pydantic import SecretStr


logger.add("services.log")


class SimplePasswordAuthService:
    def __init__(
        self,
        session: AsyncSession,
        auth_dao: SimplePasswordAuthDAO,
        user_client: UserApiClient,
    ) -> None:
        self.session = session
        self.auth_dao = auth_dao
        self.user_client = user_client

    async def authenticate(self, username: str, password: SecretStr):
        user_id = await self.user_client.get_user_id(username)
        if not user_id:
            logger.info("User does not exist")
            return False

        if type(password) is str:
            password = SecretStr(password)

        auth_status = await self.auth_dao.authenticate(
            user_id, password.get_secret_value()
        )
        if auth_status:
            logger.info("User authenticated successfully, Generating token")
            token = generate_token()
            logger.info("Token generated")
            return token

        logger.info("Invalid username or password, User not authenticated")
        return

    async def create_auth_user(self, user_id: int, password: SecretStr):
        auth = await self.auth_dao.create_user(user_id, password.get_secret_value())
        return auth
