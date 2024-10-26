import secrets
import string
from datetime import timedelta
from typing import TYPE_CHECKING

from loguru import logger
from redis.asyncio import Redis

if TYPE_CHECKING:
    RedisType = Redis[str]  # this is only processed by mypy
else:
    RedisType = Redis  # this is not seen by mypy but will be executed at runtime


def generate_token(length: int = 32) -> str:
    """Generate a secure random session token.

    Args:
        length (int): The length of the token. Default is 32 characters.

    Returns:
        str: A secure random session token.
    """
    # Define the character set: letters and digits
    characters = string.ascii_letters + string.digits

    # Generate a secure random token
    token = "".join(secrets.choice(characters) for _ in range(length))

    return token


# async def set_token(db_instance, key, user_info: dict):
#     logger.debug(f"key: {key}, data={user_info}")
#     await db_instance.hset(key, mapping=user_info)
#     await db_instance.expire(key, 3600)

#     return


async def set_token(
    redis_instance: RedisType,
    user_id: str,
    access_token: str,
    expires_delta: timedelta,
) -> None:
    # Convert timedelta to seconds
    expires = int(expires_delta.total_seconds())
    # Store the token as the key and the user_id as the value
    logger.info(f"user_id: {user_id}, access_token: {access_token}, expires: {expires}")
    await redis_instance.set(name=access_token, value=str(user_id), ex=expires)


async def get_token(redis_instance: RedisType, token: str) -> dict[str, object] | None:
    # We're now searching for the token itself, not the user_id
    user_id = await redis_instance.get(token)
    logger.info(f"user_id: {user_id}")
    if not user_id:
        print(f"No user found for token: {token}")
        return None

    return {"user_id": user_id}


if __name__ == "__main__":
    # Example usage
    session_token = generate_token()
    print(session_token)  # Output: A secure random token of the specified length
