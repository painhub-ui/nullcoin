from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any

from ..chain.transaction import Transaction, TxInput, TxOutput
from ..crypto.keys import PrivateKey, PublicKey


@dataclass
class UTXO:
    tx_id: str
    output_index: int
    amount: float
    address: str


class Wallet:

    def __init__(self) -> None:
        self._private_key = PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._address = self._public_key.to_address()
        self._label = ""

    @classmethod
    def from_private_key(cls, hex_key: str) -> Wallet:
        wallet = cls.__new__(cls)
        wallet._private_key = PrivateKey.from_hex(hex_key)
        wallet._public_key = wallet._private_key.public_key()
        wallet._address = wallet._public_key.to_address()
        wallet._label = ""
        return wallet

    @property
    def address(self) -> str:
        return self._address

    @property
    def public_key(self) -> str:
        return self._public_key.to_hex()

    @property
    def private_key(self) -> str:
        return self._private_key.to_hex()

    def sign_transaction(self, tx: Transaction) -> Transaction:
        tx_data = json.dumps(tx.to_dict(), sort_keys=True).encode()
        signature = self._private_key.sign(tx_data)

        for inp in tx.inputs:
            inp.signature = signature.hex()

        return tx

    def create_transaction(
        self,
        recipient: str,
        amount: float,
        utxos: list[UTXO],
        fee: float = 0.01,
    ) -> Transaction | None:
        total_needed = amount + fee
        selected = []
        total_selected = 0.0

        for utxo in utxos:
            if utxo.address != self._address:
                continue
            selected.append(utxo)
            total_selected += utxo.amount
            if total_selected >= total_needed:
                break

        if total_selected < total_needed:
            return None

        inputs = [
            TxInput(tx_id=u.tx_id, output_index=u.output_index)
            for u in selected
        ]

        outputs = [TxOutput(amount=amount, address=recipient)]

        change = total_selected - total_needed
        if change > 0:
            outputs.append(TxOutput(amount=change, address=self._address))

        tx = Transaction(inputs=inputs, outputs=outputs, fee=fee)
        return self.sign_transaction(tx)

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self._address,
            "public_key": self._public_key.to_hex(),
        }

    def save(self, path: str) -> None:
        data = {
            "address": self._address,
            "public_key": self._public_key.to_hex(),
            "private_key": self._private_key.to_hex(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Wallet saved: {path}")
        print("KEEP YOUR PRIVATE KEY SAFE — NEVER SHARE IT")

    @classmethod
    def load(cls, path: str) -> Wallet:
        with open(path) as f:
            data = json.load(f)
        return cls.from_private_key(data["private_key"])
