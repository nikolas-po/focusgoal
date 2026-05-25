"""Тесты EncryptionService (ТЗ — безопасность AES-256)"""
import pytest
from src.services.encryption_service import EncryptionService


class TestEncryptionService:
    def test_encrypt_decrypt_roundtrip(self):
        svc = EncryptionService("TestPassword123")
        data = b"Hello, FocusGoal!"
        encrypted = svc.encrypt(data)
        decrypted = svc.decrypt(encrypted)
        assert decrypted == data

    def test_encrypted_differs_from_original(self):
        svc = EncryptionService("TestPassword123")
        data = b"Secret data"
        encrypted = svc.encrypt(data)
        assert encrypted != data

    def test_different_passwords_differ(self):
        svc1 = EncryptionService("Password1!")
        svc2 = EncryptionService("Password2@")
        data = b"Same data"
        enc1 = svc1.encrypt(data)
        enc2 = svc2.encrypt(data)
        assert enc1 != enc2

    def test_same_password_same_salt_reproducible(self):
        svc1 = EncryptionService("SamePass123", salt=b"\x00" * 16)
        svc2 = EncryptionService("SamePass123", salt=b"\x00" * 16)
        data = b"Test data"
        assert svc1.encrypt(data) != data
        assert svc2.decrypt(svc1.encrypt(data)) == data

    def test_wrong_password_decryption_fails(self):
        svc_enc = EncryptionService("CorrectPass1")
        svc_dec = EncryptionService("WrongPass123", salt=svc_enc.salt)
        data = b"Secret"
        encrypted = svc_enc.encrypt(data)
        with pytest.raises(Exception):
            svc_dec.decrypt(encrypted)

    def test_unicode_data(self):
        svc = EncryptionService("TestPass123!")
        data = "Привет, мир! 🎯".encode("utf-8")
        assert svc.decrypt(svc.encrypt(data)) == data

    def test_large_data(self):
        svc = EncryptionService("TestPass123!")
        data = b"x" * 100_000
        assert svc.decrypt(svc.encrypt(data)) == data

    def test_utils_encrypt_decrypt_roundtrip(self):
        from src.utils.encryption import encrypt_bytes, decrypt_bytes

        data = b"Hello, FocusGoal!"
        encrypted = encrypt_bytes(data, "TestPassword123")
        assert encrypted != data
        assert decrypt_bytes(encrypted, "TestPassword123") == data

    def test_utils_decrypt_with_wrong_password_fails(self):
        from src.utils.encryption import encrypt_bytes, decrypt_bytes

        encrypted = encrypt_bytes(b"Secret message", "CorrectPass1")
        with pytest.raises(Exception):
            decrypt_bytes(encrypted, "WrongPass123")
