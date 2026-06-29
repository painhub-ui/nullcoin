import sys
sys.path.insert(0, 'src')

import pytest
from ecdsa import SECP256k1
from nullcoin.crypto import PedersenCommitment, PrivacyEngine
from nullcoin.crypto.pedersen import Commitment

ORDER = SECP256k1.order


def test_commitment_hides_amount():
    c1 = PedersenCommitment.commit(100)
    c2 = PedersenCommitment.commit(100)
    assert c1.to_hex() != c2.to_hex()


def test_commitment_deterministic_with_blinding():
    bf = PedersenCommitment.generate_blinding_factor()
    c1 = PedersenCommitment.commit(100, bf)
    c2 = PedersenCommitment.commit(100, bf)
    assert c1.to_hex() == c2.to_hex()


def test_sum_verification_single():
    bf_in = PedersenCommitment.generate_blinding_factor()
    bf_out = bf_in
    c_in = PedersenCommitment.commit(50, bf_in)
    c_out = PedersenCommitment.commit(50, bf_out)
    assert PedersenCommitment.verify_sum([c_in], [c_out])


def test_sum_verification_multiple_inputs():
    bf1 = PedersenCommitment.generate_blinding_factor()
    bf2 = PedersenCommitment.generate_blinding_factor()
    bf_out = (bf1 + bf2) % ORDER

    c_in1 = PedersenCommitment.commit(30, bf1)
    c_in2 = PedersenCommitment.commit(70, bf2)
    c_out = PedersenCommitment.commit(100, bf_out)

    assert PedersenCommitment.verify_sum([c_in1, c_in2], [c_out])


def test_sum_verification_fails_wrong_amount():
    bf = PedersenCommitment.generate_blinding_factor()
    c_in = PedersenCommitment.commit(100, bf)
    c_out = PedersenCommitment.commit(99, bf)
    assert not PedersenCommitment.verify_sum([c_in], [c_out])


def test_private_transaction_balanced():
    engine = PrivacyEngine()
    bf = PedersenCommitment.generate_blinding_factor()

    tx = engine.create_private_transaction(
        sender_address="NLC_sender",
        recipient_address="NLC_recipient",
        amount=30,
        fee=1,
        input_tx_id="a" * 64,
        input_index=0,
        input_amount=50,
        input_blinding=bf,
    )

    assert tx is not None
    assert tx.is_balanced()


def test_private_transaction_correct_outputs():
    engine = PrivacyEngine()
    bf = PedersenCommitment.generate_blinding_factor()

    tx = engine.create_private_transaction(
        sender_address="NLC_sender",
        recipient_address="NLC_recipient",
        amount=30,
        fee=1,
        input_tx_id="a" * 64,
        input_index=0,
        input_amount=50,
        input_blinding=bf,
    )

    assert tx is not None
    assert len(tx.outputs) == 2
    assert tx.outputs[0].amount == 30
    assert tx.outputs[0].address == "NLC_recipient"
    assert tx.outputs[1].amount == 19
    assert tx.outputs[1].address == "NLC_sender"


def test_private_transaction_insufficient_funds():
    engine = PrivacyEngine()
    bf = PedersenCommitment.generate_blinding_factor()

    tx = engine.create_private_transaction(
        sender_address="NLC_sender",
        recipient_address="NLC_recipient",
        amount=100,
        fee=1,
        input_tx_id="a" * 64,
        input_index=0,
        input_amount=50,
        input_blinding=bf,
    )

    assert tx is None


def test_private_transaction_no_change():
    engine = PrivacyEngine()
    bf = PedersenCommitment.generate_blinding_factor()

    tx = engine.create_private_transaction(
        sender_address="NLC_sender",
        recipient_address="NLC_recipient",
        amount=49,
        fee=1,
        input_tx_id="a" * 64,
        input_index=0,
        input_amount=50,
        input_blinding=bf,
    )

    assert tx is not None
    assert len(tx.outputs) == 1
    assert tx.outputs[0].amount == 49
    assert tx.is_balanced()


def test_commitment_to_hex_and_back():
    bf = PedersenCommitment.generate_blinding_factor()
    c = PedersenCommitment.commit(42, bf)
    hex_str = c.to_hex()
    restored = Commitment.from_hex(hex_str)
    assert restored.point == c.point
