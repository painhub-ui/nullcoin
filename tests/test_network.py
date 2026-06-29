import sys
sys.path.insert(0, 'src')

import time
import pytest
from nullcoin.chain import Blockchain
from nullcoin.network import Node, Message, MessageType


def make_chain(miner: str | None = None) -> Blockchain:
    chain = Blockchain()
    if miner:
        chain.initialize(miner)
    return chain


def test_message_serialize_deserialize():
    msg = Message.handshake(port=9333, height=5)
    raw = msg.to_bytes()
    restored = Message.from_bytes(raw)
    assert restored.type == MessageType.HANDSHAKE
    assert restored.payload["port"] == 9333
    assert restored.payload["height"] == 5


def test_message_ping_pong():
    ping = Message.ping()
    pong = Message.pong()
    assert ping.type == MessageType.PING
    assert pong.type == MessageType.PONG


def test_message_new_block():
    chain = make_chain("NLC_test")
    block = chain.last_block
    msg = Message.new_block(block.to_dict())
    assert msg.type == MessageType.NEW_BLOCK
    assert "block" in msg.payload


def test_node_starts_and_stops():
    chain = make_chain("NLC_test")
    node = Node(host="127.0.0.1", port=9340, blockchain=chain)
    node.start()
    time.sleep(0.2)
    assert node._running
    node.stop()
    assert not node._running


def test_two_nodes_connect():
    chain1 = make_chain("NLC_miner1")
    chain2 = make_chain()

    node1 = Node(host="127.0.0.1", port=9341, blockchain=chain1)
    node2 = Node(host="127.0.0.1", port=9342, blockchain=chain2)

    node1.start()
    node2.start()
    time.sleep(0.3)

    connected = node2.connect_to_peer("127.0.0.1", 9341)
    time.sleep(2)

    assert connected
    assert node1.peer_count >= 1
    assert node2.peer_count >= 1

    node1.stop()
    node2.stop()


def test_chain_sync():
    chain1 = make_chain("NLC_miner1")
    chain2 = make_chain()

    node1 = Node(host="127.0.0.1", port=9343, blockchain=chain1)
    node2 = Node(host="127.0.0.1", port=9344, blockchain=chain2)

    node1.start()
    node2.start()
    time.sleep(0.3)

    node2.connect_to_peer("127.0.0.1", 9343)
    time.sleep(3)

    assert node2.blockchain.height == node1.blockchain.height
    assert node2.blockchain.last_block.hash == node1.blockchain.last_block.hash

    node1.stop()
    node2.stop()


def test_block_broadcast():
    chain1 = make_chain("NLC_miner1")
    chain2 = make_chain()

    node1 = Node(host="127.0.0.1", port=9345, blockchain=chain1)
    node2 = Node(host="127.0.0.1", port=9346, blockchain=chain2)

    node1.start()
    node2.start()
    time.sleep(0.3)

    node2.connect_to_peer("127.0.0.1", 9345)
    time.sleep(3)

    assert node2.blockchain.height == 1

    node1.stop()
    node2.stop()
