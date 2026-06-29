from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from ecdsa import SECP256k1
from ecdsa.ellipticcurve import Point


CURVE = SECP256k1.curve
ORDER = SECP256k1.order
GENERATOR = SECP256k1.generator


def _hash_to_point(data: bytes) -> Point:
    h = hashlib.sha256(data).digest()
    x = int.from_bytes(h, "big") % CURVE.p()
    while True:
        y_sq = (pow(x, 3, CURVE.p()) + CURVE.a() * x + CURVE.b()) % CURVE.p()
        y = pow(y_sq, (CURVE.p() + 1) // 4, CURVE.p())
        if pow(y, 2, CURVE.p()) == y_sq:
            return Point(CURVE, x, y)
        x = (x + 1) % CURVE.p()


H_POINT = _hash_to_point(b"NullCoin_Pedersen_H_Generator_v1")


@dataclass
class Commitment:
    point: Point
    blinding_factor: int

    def to_hex(self) -> str:
        x = self.point.x()
        y = self.point.y()
        return f"{x:064x}{y:064x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> Commitment:
        x = int(hex_str[:64], 16)
        y = int(hex_str[64:], 16)
        point = Point(CURVE, x, y)
        return cls(point=point, blinding_factor=0)


class PedersenCommitment:

    @staticmethod
    def commit(amount: int, blinding_factor: int | None = None) -> Commitment:
        if blinding_factor is None:
            blinding_factor = secrets.randbelow(ORDER)

        r_G = GENERATOR * blinding_factor
        v_H = H_POINT * amount
        commitment_point = r_G + v_H

        return Commitment(
            point=commitment_point,
            blinding_factor=blinding_factor,
        )

    @staticmethod
    def verify_sum(
        input_commitments: list[Commitment],
        output_commitments: list[Commitment],
        fee_commitment: Commitment | None = None,
    ) -> bool:
        input_sum = None
        for c in input_commitments:
            if input_sum is None:
                input_sum = c.point
            else:
                input_sum = input_sum + c.point

        output_sum = None
        for c in output_commitments:
            if output_sum is None:
                output_sum = c.point
            else:
                output_sum = output_sum + c.point

        if fee_commitment is not None:
            if output_sum is None:
                output_sum = fee_commitment.point
            else:
                output_sum = output_sum + fee_commitment.point

        if input_sum is None or output_sum is None:
            return False

        return input_sum == output_sum

    @staticmethod
    def generate_blinding_factor() -> int:
        return secrets.randbelow(ORDER)

    @staticmethod
    def combine_blinding_factors(factors: list[int]) -> int:
        total = sum(factors) % ORDER
        return total
