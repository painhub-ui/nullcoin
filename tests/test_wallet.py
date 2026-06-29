import sys
sys.path.insert(0, 'src')

import pytest
from nullcoin.wallet import Wallet, UTXO
from nullcoin.crypto import PrivateKey, PublicKey


def test_wallet_generates_address():
    wallet = Wallet()
    assert wallet.address.startswith("NLC")
    assert len(wallet.address) > 10


def test_wallet_restore_from_private_key():
    wallet = Wallet()
    restored = Wallet.from_private_key(wallet.private_key)
    assert wallet.address == restored.address
    assert wallet.public_key == restored.public_key


def test_two_wallets_different_address():
    w1 = Wallet()
    w2 = Wallet()
    assert w1.address != w2.address
    assert w1.private_key != w2.private_key


def test_sign_and_verify():
    key = PrivateKey.generate()
    pub = key.public_key()
    data = b"NullCoin test transaction"
    sig = key.sign(data)
    assert pub.verify(sig, data)


def test_wrong_signature_fails():
    key = PrivateKey.generate()
    pub = key.public_key()
    data = b"NullCoin test transaction"
    sig = key.sign(data)
    assert not pub.verify(sig, b"tampered data")


def test_wallet_create_transaction():
    sender = Wallet()
    recipient = Wallet()

    utxos = [
        UTXO(
            tx_id="a" * 64,
            output_index=0,
            amount=10.0,
            address=sender.address,
        )
    ]

    tx = sender.create_transaction(
        recipient=recipient.address,
        amount=5.0,
        utxos=utxos,
        fee=0.01,
    )

    assert tx is not None
    assert len(tx.outputs) == 2
    assert tx.outputs[0].amount == 5.0
    assert tx.outputs[0].address == recipient.address
    assert tx.outputs[1].address == sender.address


def test_wallet_insufficient_funds():
    sender = Wallet()
    recipient = Wallet()

    utxos = [
        UTXO(
            tx_id="b" * 64,
            output_index=0,
            amount=1.0,
            address=sender.address,
        )
    ]

    tx = sender.create_transaction(
        recipient=recipient.address,
        amount=10.0,
        utxos=utxos,
        fee=0.01,
    )

    assert tx is None


def test_transaction_is_signed():
    sender = Wallet()
    recipient = Wallet()

    utxos = [
        UTXO(
            tx_id="c" * 64,
            output_index=0,
            amount=5.0,
            address=sender.address,
        )
    ]

    tx = sender.create_transaction(
        recipient=recipient.address,
        amount=2.0,
        utxos=utxos,
    )

    assert tx is not None
    for inp in tx.inputs:
        assert inp.signature != ""


def test_public_key_to_address_consistent():
    key = PrivateKey.generate()
    pub = key.public_key()
    addr1 = pub.to_address()
    addr2 = pub.to_address()
    assert addr1 == addr2
    assert addr1.startswith("NLC")
