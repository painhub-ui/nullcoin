from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from typing import Any

from .pedersen import Commitment, PedersenCommitment


@dataclass
class PrivateInput:
    tx_id: str
    output_index: int
    amount: int
    commitment: Commitment
    blinding_factor: int
    signature: str = ""


@dataclass
class PrivateOutput:
    commitment: Commitment
    blinding_factor: int
    amount: int
    address: str
    range_proof: str = ""


@dataclass
class PrivateTransaction:
    inputs: list[PrivateInput]
    outputs: list[PrivateOutput]
    tx_id: str = ""
    fee: int = 0
    fee_commitment: Commitment | None = None

    def __post_init__(self) -> None:
        if not self.tx_id:
            self.tx_id = self._compute_id()

    def _compute_id(self) -> str:
        data = (
            str([i.tx_id for i in self.inputs])
            + str([o.commitment.to_hex() for o in self.outputs])
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def is_balanced(self) -> bool:
        input_commitments = [i.commitment for i in self.inputs]
        output_commitments = [o.commitment for o in self.outputs]
        return PedersenCommitment.verify_sum(
            input_commitments,
            output_commitments,
            self.fee_commitment,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "fee": self.fee,
            "inputs": [
                {
                    "tx_id": i.tx_id,
                    "output_index": i.output_index,
                    "commitment": i.commitment.to_hex(),
                    "signature": i.signature,
                }
                for i in self.inputs
            ],
            "outputs": [
                {
                    "commitment": o.commitment.to_hex(),
                    "address": o.address,
                    "range_proof": o.range_proof,
                }
                for o in self.outputs
            ],
        }


class PrivacyEngine:

    def __init__(self) -> None:
        self._pedersen = PedersenCommitment()

    def create_private_transaction(
        self,
        sender_address: str,
        recipient_address: str,
        amount: int,
        fee: int,
        input_tx_id: str,
        input_index: int,
        input_amount: int,
        input_blinding: int,
    ) -> PrivateTransaction | None:
        from ecdsa import SECP256k1
        ORDER = SECP256k1.order

        if input_amount < amount + fee:
            return None

        input_commitment = PedersenCommitment.commit(
            input_amount, input_blinding
        )

        recipient_blinding = PedersenCommitment.generate_blinding_factor()
        recipient_commitment = PedersenCommitment.commit(
            amount, recipient_blinding
        )

        change = input_amount - amount - fee
        outputs = [
            PrivateOutput(
                commitment=recipient_commitment,
                blinding_factor=recipient_blinding,
                amount=amount,
                address=recipient_address,
                range_proof=self._simple_range_proof(amount),
            )
        ]

        total_output_blinding = recipient_blinding

        if change > 0:
            change_blinding = PedersenCommitment.generate_blinding_factor()
            change_commitment = PedersenCommitment.commit(
                change, change_blinding
            )
            outputs.append(
                PrivateOutput(
                    commitment=change_commitment,
                    blinding_factor=change_blinding,
                    amount=change,
                    address=sender_address,
                    range_proof=self._simple_range_proof(change),
                )
            )
            total_output_blinding = (
                recipient_blinding + change_blinding
            ) % ORDER

        fee_blinding = (
            input_blinding - total_output_blinding
        ) % ORDER

        fee_commitment = PedersenCommitment.commit(fee, fee_blinding)

        priv_input = PrivateInput(
            tx_id=input_tx_id,
            output_index=input_index,
            amount=input_amount,
            commitment=input_commitment,
            blinding_factor=input_blinding,
        )

        tx = PrivateTransaction(
            inputs=[priv_input],
            outputs=outputs,
            fee=fee,
            fee_commitment=fee_commitment,
        )

        return tx

    def _simple_range_proof(self, amount: int) -> str:
        proof_data = f"range_proof:amount_positive:{amount > 0}:{amount < 2**64}"
        return hashlib.sha256(proof_data.encode()).hexdigest()
