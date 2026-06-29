from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    GET_PEERS = "get_peers"
    PEERS = "peers"
    GET_BLOCKS = "get_blocks"
    BLOCKS = "blocks"
    NEW_BLOCK = "new_block"
    NEW_TRANSACTION = "new_transaction"
    GET_CHAIN_INFO = "get_chain_info"
    CHAIN_INFO = "chain_info"
    PING = "ping"
    PONG = "pong"


@dataclass
class Message:
    type: MessageType
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    version: int = 1

    def to_bytes(self) -> bytes:
        data = {
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "version": self.version,
        }
        return json.dumps(data).encode() + b"\n"

    @classmethod
    def from_bytes(cls, data: bytes) -> Message:
        parsed = json.loads(data.decode().strip())
        return cls(
            type=MessageType(parsed["type"]),
            payload=parsed.get("payload", {}),
            timestamp=parsed.get("timestamp", time.time()),
            version=parsed.get("version", 1),
        )

    @classmethod
    def handshake(cls, port: int, height: int) -> Message:
        return cls(
            type=MessageType.HANDSHAKE,
            payload={"port": port, "height": height, "coin": "NLC"},
        )

    @classmethod
    def handshake_ack(cls, port: int, height: int) -> Message:
        return cls(
            type=MessageType.HANDSHAKE_ACK,
            payload={"port": port, "height": height, "coin": "NLC"},
        )

    @classmethod
    def ping(cls) -> Message:
        return cls(type=MessageType.PING, payload={})

    @classmethod
    def pong(cls) -> Message:
        return cls(type=MessageType.PONG, payload={})

    @classmethod
    def get_peers(cls) -> Message:
        return cls(type=MessageType.GET_PEERS, payload={})

    @classmethod
    def peers(cls, peer_list: list[dict]) -> Message:
        return cls(type=MessageType.PEERS, payload={"peers": peer_list})

    @classmethod
    def get_chain_info(cls) -> Message:
        return cls(type=MessageType.GET_CHAIN_INFO, payload={})

    @classmethod
    def chain_info(cls, height: int, last_hash: str) -> Message:
        return cls(
            type=MessageType.CHAIN_INFO,
            payload={"height": height, "last_hash": last_hash},
        )

    @classmethod
    def new_block(cls, block_data: dict) -> Message:
        return cls(
            type=MessageType.NEW_BLOCK,
            payload={"block": block_data},
        )

    @classmethod
    def new_transaction(cls, tx_data: dict) -> Message:
        return cls(
            type=MessageType.NEW_TRANSACTION,
            payload={"transaction": tx_data},
        )

    @classmethod
    def get_blocks(cls, from_height: int) -> Message:
        return cls(
            type=MessageType.GET_BLOCKS,
            payload={"from_height": from_height},
        )

    @classmethod
    def blocks(cls, blocks_data: list[dict]) -> Message:
        return cls(
            type=MessageType.BLOCKS,
            payload={"blocks": blocks_data},
        )
