from __future__ import annotations

import hashlib
import os
import secrets

from ecdsa import SECP256k1, SigningKey, VerifyingKey


class PrivateKey:

    def __init__(self, raw: bytes | None = None) -> None:
        if raw:
            self._key = SigningKey.from_string(raw, curve=SECP256k1)
        else:
            self._key = SigningKey.generate(curve=SECP256k1)

    @classmethod
    def generate(cls) -> PrivateKey:
        return cls()

    @classmethod
    def from_hex(cls, hex_str: str) -> PrivateKey:
        return cls(raw=bytes.fromhex(hex_str))

    def to_hex(self) -> str:
        return self._key.to_string().hex()

    def to_bytes(self) -> bytes:
        return self._key.to_string()

    def public_key(self) -> PublicKey:
        return PublicKey(self._key.get_verifying_key())

    def sign(self, data: bytes) -> bytes:
        return self._key.sign(data)


class PublicKey:

    def __init__(self, key: VerifyingKey) -> None:
        self._key = key

    @classmethod
    def from_hex(cls, hex_str: str) -> PublicKey:
        key = VerifyingKey.from_string(
            bytes.fromhex(hex_str),
            curve=SECP256k1,
        )
        return cls(key)

    def to_hex(self) -> str:
        return self._key.to_string().hex()

    def to_bytes(self) -> bytes:
        return self._key.to_string()

    def verify(self, signature: bytes, data: bytes) -> bool:
        try:
            return self._key.verify(signature, data)
        except Exception:
            return False

    def to_address(self) -> str:
        pub_bytes = self.to_bytes()
        sha256 = hashlib.sha256(pub_bytes).digest()
        ripemd160 = hashlib.new("ripemd160", sha256).digest()
        checksum = hashlib.sha256(
            hashlib.sha256(ripemd160).digest()
        ).digest()[:4]
        raw = ripemd160 + checksum
        return "NLC" + raw.hex()
