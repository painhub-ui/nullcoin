import sys
sys.path.insert(0, 'src')

import pytest
from nullcoin.chain import Blockchain, Transaction, TxInput, TxOutput


MINER = "NLC_test_miner"


def test_genesis_block():
    chain = Blockchain()
    genesis = chain.initialize(MINER)

    assert chain.height == 1
    assert genesis.header.height == 0
    assert genesis.header.previous_hash == "0" * 64
    assert chain.is_valid_chain()


def test_block_reward():
    chain = Blockchain()
    chain.initialize(MINER)

    reward = chain.get_block_reward(0)
    assert reward == 6.0

    reward_after_halving = chain.get_block_reward(210_000)
    assert reward_after_halving == 3.0

    tail = chain.get_block_reward(999_999_999)
    assert tail == 0.1


def test_mine_block():
    chain = Blockchain()
    chain.initialize(MINER)

    block = chain.mine_pending(MINER)

    assert block is not None
    assert chain.height == 2
    assert chain.is_valid_chain()


def test_balance_tracking():
    chain = Blockchain()
    chain.initialize(MINER)
    chain.mine_pending(MINER)

    balance = chain.get_balance(MINER)
    assert balance == 12.0


def test_chain_validity():
    chain = Blockchain()
    chain.initialize(MINER)
    chain.mine_pending(MINER)

    assert chain.is_valid_chain()


def test_transaction_in_block():
    chain = Blockchain()
    chain.initialize(MINER)

    tx = Transaction(
        inputs=[TxInput(tx_id="0" * 64, output_index=0)],
        outputs=[
            TxOutput(amount=2.0, address="NLC_recipient"),
        ],
    )

    chain.add_transaction(tx)
    assert chain.pending_count == 1

    chain.mine_pending(MINER)
    assert chain.pending_count == 0
    assert chain.height == 2


def test_total_supply_tracking():
    chain = Blockchain()
    chain.initialize(MINER)

    assert chain.total_minted == 6.0

    chain.mine_pending(MINER)
    assert chain.total_minted == 12.0
