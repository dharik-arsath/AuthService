from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.exceptions import UserCreationFailed
from auth.models import AuthModel


class SimplePasswordAuthDAO:
    def __init__(self, session: AsyncSession, model: type[AuthModel] = AuthModel):
        self.session = session
        self.model = model

    async def authenticate(self, user_id: str, password: str) -> Optional[AuthModel]:
        # optimize query by selecting only relevant field

        query = select(self.model).where(self.model.user_id == user_id)  # type: ignore
        result = await self.session.execute(query)
        user = result.scalars().first()
        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user.password.encode("utf-8"),
        ):
            return user

        else:
            return None

    async def create_user(self, user_id: str, password: str) -> AuthModel:
        try:
            auth = self.model(user_id=user_id, password=password)
            self.session.add(auth)
            return auth
        except IntegrityError as e:
            raise UserCreationFailed(str(e))

    async def is_user_id_exist(self, user_id: int) -> bool:
        query = select(self.model).filter(self.model.user_id == user_id).limit(1)  # type: ignore
        result = await self.session.execute(query)
        exists = result.scalars().first() is not None
        return exists
