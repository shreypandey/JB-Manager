import os
from cryptography.fernet import Fernet


class EncryptionHandler:
    encryption_key = os.getenv("ENCRYPTION_KEY")

    @classmethod
    def encrypt_text(cls, text: str) -> str:
        f = Fernet(cls.encryption_key)
        return f.encrypt(text.encode()).decode()

    @classmethod
    def decrypt_text(cls, text: str) -> str:
        f = Fernet(cls.encryption_key)
        return f.decrypt(text.encode()).decode()

    @classmethod
    def encrypt_dict(cls, data: dict) -> dict:
        f = Fernet(cls.encryption_key)
        return {key: f.encrypt(value.encode()).decode() for key, value in data.items()}
