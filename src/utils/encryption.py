"""Утилита шифрования (обёртка над EncryptionService)"""
from src.services.encryption_service import EncryptionService


def encrypt_bytes(data: bytes, password: str) -> bytes:
    svc = EncryptionService(password)
    return b"FGENC" + svc.salt + svc.encrypt(data)


def decrypt_bytes(data: bytes, password: str) -> bytes:
    if data[:5] != b"FGENC":
        raise ValueError("Данные не зашифрованы или повреждены")
    salt = data[5:21]
    encrypted = data[21:]
    svc = EncryptionService(password, salt)
    return svc.decrypt(encrypted)
