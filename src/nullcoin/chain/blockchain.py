from __future__ import annotations

import json
import os
import time
from typing import Any

from .block import Block
from .constants import (
    DIFFICULTY_ADJUSTMENT_INTERVAL,
    DIFFICULTY_INITIAL,
    BLOCK_TIME_SECONDS,
    GENESIS_MESSAGE,
    HALVING_INTERVAL,
    INITIAL_REWARD,
    TAIL_EMISSION,
    TOTAL_SUPPLY,
)
from .miner import Miner
from .transaction import Transaction


class Blockchain:

    def __init__(self) -> None:
        self._chain: list[Block] = []
        self._pending: list[Transaction] = []
        self._difficulty = DIFFICULTY_INITIAL
        self._total_minted = 0.0

    def initialize(self, miner_address: str) -> Block:
        genesis = Block.genesis(miner_address, GENESIS_MESSAGE)
        miner = Miner(miner_address)
        genesis = miner.mine(genesis)
        self._chain.append(genesis)
        self._total_minted += self.get_block_reward(0)
        return genesis

    def add_transaction(self, tx: Transaction) -> None:
        self._pending.append(tx)

    def mine_pending(self, miner_address: str) -> Block | None:
        if not self._chain:
            return None

        miner = Miner(miner_address)
        height = len(self._chain)
        reward = self.get_block_reward(height)
        difficulty = self._get_difficulty()

        block = miner.create_block(
            previous_hash=self._chain[-1].hash,
            height=height,
            transactions=self._pending.copy(),
            reward=reward,
            difficulty=difficulty,
        )

        block = miner.mine(block)

        if self._is_valid_block(block):
            self._chain.append(block)
            self._pending = []
            self._total_minted += reward
            return block

        return None

    def get_block_reward(self, height: int) -> float:
        halvings = min(height // HALVING_INTERVAL, 64)
        reward = INITIAL_REWARD / (2 ** halvings)
        return max(reward, TAIL_EMISSION)

    def get_balance(self, address: str) -> float:
        balance = 0.0
        spent = set()

        for block in self._chain:
            for tx in block.transactions:
                for inp in tx.inputs:
                    spent.add((inp.tx_id, inp.output_index))

        for block in self._chain:
            for tx in block.transactions:
                for i, out in enumerate(tx.outputs):
                    if out.address == address:
                        if (tx.tx_id, i) not in spent:
                            balance += out.amount

        return balance

    def is_valid_chain(self) -> bool:
        for i in range(1, len(self._chain)):
            current = self._chain[i]
            previous = self._chain[i - 1]

            if current.hash != current.compute_hash():
                return False

            if current.header.previous_hash != previous.hash:
                return False

            if not current.is_valid_proof():
                return False

        return True

    def _is_valid_block(self, block: Block) -> bool:
        if not self._chain:
            return True

        last = self._chain[-1]

        if block.header.previous_hash != last.hash:
            return False

        if block.compute_hash() != block.hash:
            return False

        if not block.is_valid_proof():
            return False

        return True

    def _get_difficulty(self) -> int:
        height = len(self._chain)

        if height < DIFFICULTY_ADJUSTMENT_INTERVAL:
            return self._difficulty

        if height % DIFFICULTY_ADJUSTMENT_INTERVAL != 0:
            return self._difficulty

        last = self._chain[-1]
        first = self._chain[-DIFFICULTY_ADJUSTMENT_INTERVAL]
        elapsed = last.header.timestamp - first.header.timestamp
        expected = BLOCK_TIME_SECONDS * DIFFICULTY_ADJUSTMENT_INTERVAL

        if elapsed < expected / 2:
            self._difficulty += 1
        elif elapsed > expected * 2:
            self._difficulty = max(1, self._difficulty - 1)

        return self._difficulty

    @property
    def height(self) -> int:
        return len(self._chain)

    @property
    def last_block(self) -> Block | None:
        return self._chain[-1] if self._chain else None

    @property
    def total_minted(self) -> float:
        return self._total_minted

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def to_dict(self) -> dict[str, Any]:
        return {
            "height": self.height,
            "difficulty": self._difficulty,
            "total_minted": self._total_minted,
            "chain": [b.to_dict() for b in self._chain],
        }

    def save(self, path: str = "nullcoin_chain.json") -> None:
        data = self.to_dict()
        data["pending"] = [tx.to_dict() for tx in self._pending]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Chain saved: {path}")
