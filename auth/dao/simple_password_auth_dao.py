from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
from auth.models import AuthModel


class SimplePasswordAuthDAO:
    def __init__(self, session: AsyncSession, model=AuthModel):
        self.session = session
        self.model = model

    async def authenticate(self, user_id: int, password: str):
        query = select(self.model).filter(self.model.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()
        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8"),
        ):
            return user

    async def create_user(self, user_id: int, password: str):
        auth = self.model(user_id=user_id, password=password)
        self.session.add(auth)
        return auth
