from cryptography.fernet import Fernet

from app.config import settings


def get_fernet() -> Fernet:
    if not settings.fernet_key:
        raise ValueError("FERNET_KEY must be set for token encryption")
    return Fernet(settings.fernet_key.encode())


def encrypt_token(token: str) -> str:
    return get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return get_fernet().decrypt(encrypted.encode()).decode()


def generate_fernet_key() -> str:
    return Fernet.generate_key().decode()
