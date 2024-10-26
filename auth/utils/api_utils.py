import asyncio
from functools import wraps
from typing import Callable


def retry_with_backoff(tries: int = 3, backoff: float = 1.0) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_tries = tries
            current_backoff = backoff
            while current_tries > 0:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    current_tries -= 1
                    if current_tries > 0:
                        print(
                            f"Error {e}, Retrying in {current_backoff} seconds... ({current_tries} tries left)"
                        )
                        await asyncio.sleep(current_backoff)
                        current_backoff *= 2  # Double the backoff for the next attempt
                    else:
                        print("All retries failed.")
                        raise e

        return wrapper

    return decorator
