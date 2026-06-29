from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TxInput:
    tx_id: str
    output_index: int
    signature: str = ""


@dataclass
class TxOutput:
    amount: float
    address: str
    commitment: str = ""


@dataclass
class Transaction:
    inputs: list[TxInput]
    outputs: list[TxOutput]
    tx_id: str = ""
    timestamp: float = field(default_factory=time.time)
    fee: float = 0.0
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.tx_id:
            self.tx_id = self._compute_id()

    def _compute_id(self) -> str:
        data = (
            str(self.timestamp)
            + str([(i.tx_id, i.output_index) for i in self.inputs])
            + str([(o.amount, o.address) for o in self.outputs])
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "timestamp": self.timestamp,
            "fee": self.fee,
            "memo": self.memo,
            "inputs": [
                {
                    "tx_id": i.tx_id,
                    "output_index": i.output_index,
                    "signature": i.signature,
                }
                for i in self.inputs
            ],
            "outputs": [
                {
                    "amount": o.amount,
                    "address": o.address,
                    "commitment": o.commitment,
                }
                for o in self.outputs
            ],
        }

    @classmethod
    def coinbase(cls, reward: float, miner_address: str) -> Transaction:
        return cls(
            inputs=[TxInput(tx_id="0" * 64, output_index=0)],
            outputs=[TxOutput(amount=reward, address=miner_address)],
            fee=0.0,
            memo="coinbase",
        )
