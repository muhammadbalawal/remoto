"""
Security utilities for session password and token generation.

Uses the ``secrets`` module for cryptographically strong random values.
"""

import secrets
import string


class SecurityUtils:
    """Cryptographically secure password and token generators."""
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate a random alphanumeric password.

        Args:
            length: Number of characters in the password.

        Returns:
            A random string of ASCII letters and digits.
        """
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a URL-safe random token.

        Args:
            length: Number of random bytes (output is longer due to base64 encoding).

        Returns:
            A URL-safe base64-encoded token string.
        """
        return secrets.token_urlsafe(length)