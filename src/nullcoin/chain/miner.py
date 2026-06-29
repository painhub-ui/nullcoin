from __future__ import annotations

import time

from .block import Block, BlockHeader
from .constants import DIFFICULTY_INITIAL
from .transaction import Transaction


class Miner:

    def __init__(self, address: str) -> None:
        self.address = address
        self.total_mined = 0

    def mine(self, block: Block) -> Block:
        target = "0" * block.header.difficulty
        start = time.perf_counter()

        while True:
            block.hash = block.compute_hash()
            if block.hash.startswith(target):
                break
            block.header.nonce += 1

        elapsed = time.perf_counter() - start
        self.total_mined += 1

        print(
            f"Block #{block.header.height} mined "
            f"nonce={block.header.nonce} "
            f"hash={block.hash[:16]}... "
            f"time={elapsed:.3f}s"
        )

        return block

    def create_block(
        self,
        previous_hash: str,
        height: int,
        transactions: list[Transaction],
        reward: float,
        difficulty: int,
    ) -> Block:
        coinbase = Transaction.coinbase(reward, self.address)
        all_transactions = [coinbase] + transactions

        header = BlockHeader(
            version=1,
            height=height,
            previous_hash=previous_hash,
            merkle_root="",
            timestamp=time.time(),
            difficulty=difficulty,
            nonce=0,
        )

        block = Block(header=header, transactions=all_transactions)
        block.header.merkle_root = block.compute_merkle_root()
        block.hash = block.compute_hash()

        return block
