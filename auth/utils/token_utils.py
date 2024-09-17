import secrets
import string


def generate_token(length=32):
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


if __name__ == "__main__":
    # Example usage
    session_token = generate_token()
    print(session_token)  # Output: A secure random token of the specified length
