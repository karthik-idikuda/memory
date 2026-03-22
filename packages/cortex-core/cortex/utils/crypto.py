"""CORTEX-X — Encryption utilities (stdlib only)."""

from __future__ import annotations
import hashlib
import hmac
import os
import struct
from typing import Optional


def derive_key(password: str, salt: Optional[bytes] = None, iterations: int = 100000) -> tuple:
    """PBKDF2-SHA256 key derivation. Returns (key, salt)."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return key, salt


def encrypt_data(data: bytes, password: str) -> bytes:
    """Encrypt data using PBKDF2 + SHA256-CTR + HMAC.

    Format: salt(16) + nonce(16) + ciphertext + hmac(32)
    """
    key, salt = derive_key(password)
    nonce = os.urandom(16)

    # SHA256-CTR stream cipher
    ciphertext = bytearray()
    for i in range(0, len(data), 32):
        counter = struct.pack("<I", i // 32)
        block_key = hashlib.sha256(key + nonce + counter).digest()
        chunk = data[i:i + 32]
        for j in range(len(chunk)):
            ciphertext.append(chunk[j] ^ block_key[j])

    # HMAC for authentication
    mac = hmac.new(key, salt + nonce + bytes(ciphertext), hashlib.sha256).digest()
    return salt + nonce + bytes(ciphertext) + mac


def decrypt_data(encrypted: bytes, password: str) -> bytes:
    """Decrypt data encrypted by encrypt_data."""
    salt = encrypted[:16]
    nonce = encrypted[16:32]
    mac = encrypted[-32:]
    ciphertext = encrypted[32:-32]

    key, _ = derive_key(password, salt)

    # Verify HMAC
    expected_mac = hmac.new(key, salt + nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("Decryption failed: invalid password or corrupted data")

    # SHA256-CTR decrypt
    plaintext = bytearray()
    for i in range(0, len(ciphertext), 32):
        counter = struct.pack("<I", i // 32)
        block_key = hashlib.sha256(key + nonce + counter).digest()
        chunk = ciphertext[i:i + 32]
        for j in range(len(chunk)):
            plaintext.append(chunk[j] ^ block_key[j])

    return bytes(plaintext)
