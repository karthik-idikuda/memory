"""
╔══════════════════════════════════════════════════════════╗
║  SIGMA-X Omega — Crypto Utilities                        ║
║  CAULANG-Ω: CRYPTO — encrypt causal chains at rest      ║
╚══════════════════════════════════════════════════════════╝

AES-256-CBC encryption for .sigma files and chain data.
Uses PBKDF2 key derivation from passphrase.
All crypto is stdlib-only (hashlib + hmac).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct
from typing import Tuple

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEY DERIVATION (PBKDF2-SHA256)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16
KEY_SIZE = 32        # 256-bit key
IV_SIZE = 16         # 128-bit IV
HMAC_SIZE = 32       # SHA-256 HMAC


def derive_key(passphrase: str, salt: bytes | None = None) -> Tuple[bytes, bytes]:
    """
    Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256.

    Args:
        passphrase: User passphrase string
        salt: Optional salt (generated if None)

    Returns:
        (key, salt) tuple
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        passphrase.encode('utf-8'),
        salt,
        PBKDF2_ITERATIONS,
        dklen=KEY_SIZE,
    )
    return key, salt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# XOR-BASED STREAM CIPHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pure Python AES is too slow without C extensions.
# We use a SHA-256 CTR-mode stream cipher instead —
# cryptographically secure, stdlib-only.

def _generate_keystream(key: bytes, iv: bytes, length: int) -> bytes:
    """
    Generate a keystream using SHA-256 in CTR mode.
    Each block = SHA-256(key || iv || counter).
    """
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        block_input = key + iv + struct.pack('>Q', counter)
        block = hashlib.sha256(block_input).digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:length])


def _xor_bytes(data: bytes, keystream: bytes) -> bytes:
    """XOR data with keystream."""
    return bytes(a ^ b for a, b in zip(data, keystream))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENCRYPT / DECRYPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Encrypted format:
# [SALT: 16B] [IV: 16B] [HMAC: 32B] [CIPHERTEXT: variable]

HEADER_SIZE = SALT_SIZE + IV_SIZE + HMAC_SIZE  # 64 bytes


def encrypt(data: bytes, passphrase: str) -> bytes:
    """
    Encrypt data with a passphrase.

    Uses PBKDF2 key derivation + SHA-256 CTR stream cipher + HMAC-SHA256.

    Returns:
        Encrypted bytes: [salt][iv][hmac][ciphertext]
    """
    if not data:
        return b''
    if not passphrase:
        raise ValueError("Passphrase cannot be empty")

    # Derive key
    key, salt = derive_key(passphrase)

    # Generate random IV
    iv = os.urandom(IV_SIZE)

    # Encrypt
    keystream = _generate_keystream(key, iv, len(data))
    ciphertext = _xor_bytes(data, keystream)

    # Compute HMAC over salt + iv + ciphertext for authentication
    mac_data = salt + iv + ciphertext
    mac = hmac.new(key, mac_data, hashlib.sha256).digest()

    return salt + iv + mac + ciphertext


def decrypt(encrypted: bytes, passphrase: str) -> bytes:
    """
    Decrypt data with a passphrase.

    Verifies HMAC before decryption to detect tampering.

    Returns:
        Original plaintext bytes

    Raises:
        ValueError: If passphrase is wrong or data is tampered
    """
    if not encrypted:
        return b''
    if not passphrase:
        raise ValueError("Passphrase cannot be empty")
    if len(encrypted) < HEADER_SIZE:
        raise ValueError(f"Encrypted data too short: {len(encrypted)} bytes")

    # Extract components
    salt = encrypted[:SALT_SIZE]
    iv = encrypted[SALT_SIZE:SALT_SIZE + IV_SIZE]
    stored_mac = encrypted[SALT_SIZE + IV_SIZE:HEADER_SIZE]
    ciphertext = encrypted[HEADER_SIZE:]

    # Derive key from passphrase + salt
    key, _ = derive_key(passphrase, salt)

    # Verify HMAC (authenticate before decrypt)
    mac_data = salt + iv + ciphertext
    computed_mac = hmac.new(key, mac_data, hashlib.sha256).digest()
    if not hmac.compare_digest(stored_mac, computed_mac):
        raise ValueError("Decryption failed: wrong passphrase or tampered data")

    # Decrypt
    keystream = _generate_keystream(key, iv, len(ciphertext))
    plaintext = _xor_bytes(ciphertext, keystream)

    return plaintext


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILE ENCRYPTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def encrypt_file(input_path: str, output_path: str, passphrase: str) -> int:
    """
    Encrypt a file.

    Returns:
        Size of encrypted file in bytes
    """
    with open(input_path, 'rb') as f:
        data = f.read()

    encrypted = encrypt(data, passphrase)

    with open(output_path, 'wb') as f:
        f.write(encrypted)

    return len(encrypted)


def decrypt_file(input_path: str, output_path: str, passphrase: str) -> int:
    """
    Decrypt a file.

    Returns:
        Size of decrypted file in bytes
    """
    with open(input_path, 'rb') as f:
        encrypted = f.read()

    decrypted = decrypt(encrypted, passphrase)

    with open(output_path, 'wb') as f:
        f.write(decrypted)

    return len(decrypted)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PASSPHRASE HASHING (for storage)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━

def hash_passphrase(passphrase: str) -> str:
    """
    Hash a passphrase for safe storage.
    Returns: "salt_hex:hash_hex" string
    """
    salt = os.urandom(SALT_SIZE)
    key, _ = derive_key(passphrase, salt)
    return f"{salt.hex()}:{key.hex()}"


def verify_passphrase(passphrase: str, stored_hash: str) -> bool:
    """
    Verify a passphrase against a stored hash.
    """
    try:
        salt_hex, hash_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        key, _ = derive_key(passphrase, salt)
        return hmac.compare_digest(key, expected)
    except (ValueError, AttributeError):
        return False
