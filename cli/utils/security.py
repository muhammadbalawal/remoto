import secrets
import string


class SecurityUtils:
    """Security utilities"""
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a random token"""
        return secrets.token_urlsafe(length)