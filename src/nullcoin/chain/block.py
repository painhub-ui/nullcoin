from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from .transaction import Transaction


@dataclass
class BlockHeader:
    version: int
    height: int
    previous_hash: str
    merkle_root: str
    timestamp: float
    difficulty: int
    nonce: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "height": self.height,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
        }


@dataclass
class Block:
    header: BlockHeader
    transactions: list[Transaction]
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        data = json.dumps(self.header.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def compute_merkle_root(self) -> str:
        if not self.transactions:
            return "0" * 64

        hashes = [tx.tx_id for tx in self.transactions]

        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                next_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(next_hash)
            hashes = next_level

        return hashes[0]

    def is_valid_proof(self) -> bool:
        target = "0" * self.header.difficulty
        return self.hash.startswith(target)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hash": self.hash,
            "header": self.header.to_dict(),
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

    @classmethod
    def genesis(cls, miner_address: str, message: str) -> Block:
        from .constants import (
            DIFFICULTY_INITIAL,
            GENESIS_MESSAGE,
            INITIAL_REWARD,
        )
        from .transaction import Transaction

        coinbase_tx = Transaction.coinbase(INITIAL_REWARD, miner_address)

        header = BlockHeader(
            version=1,
            height=0,
            previous_hash="0" * 64,
            merkle_root=coinbase_tx.tx_id,
            timestamp=time.time(),
            difficulty=DIFFICULTY_INITIAL,
            nonce=0,
        )

        block = cls(header=header, transactions=[coinbase_tx])
        block.header.merkle_root = block.compute_merkle_root()
        block.hash = block.compute_hash()
        return block
