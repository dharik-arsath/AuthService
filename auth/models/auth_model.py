# from database import Base
# from sqlalchemy.orm import Mapped, relationship, mapped_column
# from sqlalchemy import String, ForeignKey


# class AuthModel(Base):
#     __tablename__ = "auth"

#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     user_id: Mapped[int] = mapped_column(
#         ForeignKey("users.id", ondelete="CASCADE"),
#         primary_key=True,
#         autoincrement=False,
#         nullable=False,
#     )
#     password: Mapped[str] = mapped_column(String(255))

#     user: Mapped["UserModel"] = relationship("UserModel", backref=None)

from sqlmodel import Field, SQLModel
from typing import Optional


class AuthModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    password: str
