from __future__ import annotations

import socket
import threading
import time
from typing import Any

from ..chain.blockchain import Blockchain
from ..chain.block import Block, BlockHeader
from ..chain.transaction import Transaction, TxInput, TxOutput
from .messages import Message, MessageType
from .peer import Peer


class Node:

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 9333,
        blockchain: Blockchain | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.blockchain = blockchain or Blockchain()
        self._peers: dict[str, Peer] = {}
        self._server: socket.socket | None = None
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(10)

        server_thread = threading.Thread(
            target=self._accept_loop,
            daemon=True,
        )
        server_thread.start()

        print(f"NullCoin node started on {self.host}:{self.port}")
        print(f"Chain height: {self.blockchain.height}")

    def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.close()
        for peer in list(self._peers.values()):
            peer.disconnect()
        print("Node stopped.")

    def connect_to_peer(self, host: str, port: int) -> bool:
        peer_id = f"{host}:{port}"
        if peer_id in self._peers:
            return True

        peer = Peer(
            host=host,
            port=port,
            on_message=self._handle_message,
            on_disconnect=self._handle_disconnect,
        )

        if not peer.connect():
            return False

        with self._lock:
            self._peers[peer_id] = peer

        peer.start_listening()

        handshake = Message.handshake(
            port=self.port,
            height=self.blockchain.height,
        )
        peer.send(handshake)

        print(f"Connected to peer: {peer_id}")
        return True

    def broadcast(self, message: Message, exclude: Peer | None = None) -> None:
        with self._lock:
            peers = list(self._peers.values())
        for peer in peers:
            if peer is not exclude and peer.is_connected:
                peer.send(message)

    def broadcast_block(self, block: Block) -> None:
        msg = Message.new_block(block.to_dict())
        self.broadcast(msg)

    def broadcast_transaction(self, tx: Transaction) -> None:
        msg = Message.new_transaction(tx.to_dict())
        self.broadcast(msg)

    def _accept_loop(self) -> None:
        while self._running:
            try:
                if self._server is None:
                    break
                self._server.settimeout(1)
                try:
                    conn, addr = self._server.accept()
                except socket.timeout:
                    continue

                peer = Peer.from_socket(
                    sock=conn,
                    addr=addr,
                    on_message=self._handle_message,
                    on_disconnect=self._handle_disconnect,
                )

                peer_id = peer.peer_id
                with self._lock:
                    self._peers[peer_id] = peer

                peer.start_listening()
                print(f"Incoming connection: {peer_id}")

            except Exception as e:
                if self._running:
                    print(f"Accept error: {e}")

    def _handle_message(self, peer: Peer, message: Message) -> None:
        t = message.type

        if t == MessageType.PING:
            peer.send(Message.pong())

        elif t == MessageType.PONG:
            peer.last_seen = time.time()

        elif t == MessageType.HANDSHAKE:
            peer.height = message.payload.get("height", 0)
            peer.port = message.payload.get("port", peer.port)
            ack = Message.handshake_ack(
                port=self.port,
                height=self.blockchain.height,
            )
            peer.send(ack)
            self._sync_if_behind(peer)

        elif t == MessageType.HANDSHAKE_ACK:
            peer.height = message.payload.get("height", 0)
            self._sync_if_behind(peer)

        elif t == MessageType.GET_PEERS:
            peer_list = [
                p.to_dict()
                for p in self._peers.values()
                if p.is_connected and p is not peer
            ]
            peer.send(Message.peers(peer_list))

        elif t == MessageType.PEERS:
            for p_data in message.payload.get("peers", []):
                h, po = p_data.get("host"), p_data.get("port")
                if h and po:
                    peer_id = f"{h}:{po}"
                    if peer_id not in self._peers:
                        threading.Thread(
                            target=self.connect_to_peer,
                            args=(h, po),
                            daemon=True,
                        ).start()

        elif t == MessageType.GET_CHAIN_INFO:
            last_hash = (
                self.blockchain.last_block.hash
                if self.blockchain.last_block
                else "0" * 64
            )
            peer.send(Message.chain_info(
                height=self.blockchain.height,
                last_hash=last_hash,
            ))

        elif t == MessageType.CHAIN_INFO:
            peer.height = message.payload.get("height", 0)
            self._sync_if_behind(peer)

        elif t == MessageType.GET_BLOCKS:
            from_height = message.payload.get("from_height", 0)
            blocks_data = [
                b.to_dict()
                for b in self.blockchain._chain[from_height:]
            ]
            peer.send(Message.blocks(blocks_data))

        elif t == MessageType.BLOCKS:
            self._process_blocks(message.payload.get("blocks", []))

        elif t == MessageType.NEW_BLOCK:
            block_data = message.payload.get("block", {})
            block = self._deserialize_block(block_data)
            if block and self._accept_block(block):
                self.broadcast(Message.new_block(block_data), exclude=peer)

        elif t == MessageType.NEW_TRANSACTION:
            tx_data = message.payload.get("transaction", {})
            tx = self._deserialize_transaction(tx_data)
            if tx:
                self.blockchain.add_transaction(tx)
                self.broadcast(
                    Message.new_transaction(tx_data),
                    exclude=peer,
                )

    def _handle_disconnect(self, peer: Peer) -> None:
        with self._lock:
            self._peers.pop(peer.peer_id, None)
        print(f"Peer disconnected: {peer.peer_id}")

    def _sync_if_behind(self, peer: Peer) -> None:
        if peer.height > self.blockchain.height:
            print(f"Syncing from {peer.peer_id} (their height: {peer.height})")
            peer.send(Message.get_blocks(self.blockchain.height))

    def _process_blocks(self, blocks_data: list[dict]) -> None:
        for block_data in blocks_data:
            block = self._deserialize_block(block_data)
            if block:
                self._accept_block(block)

    def _accept_block(self, block: Block) -> bool:
        if block.header.height == 0:
            if not self.blockchain._chain:
                if block.is_valid_proof():
                    self.blockchain._chain.append(block)
                    reward = self.blockchain.get_block_reward(0)
                    self.blockchain._total_minted += reward
                    print(f"Genesis block accepted {block.hash[:16]}...")
                    return True
            return False

        if not self.blockchain._chain:
            return False

        last = self.blockchain.last_block
        if block.header.height != last.header.height + 1:
            return False
        if block.header.previous_hash != last.hash:
            return False
        if not block.is_valid_proof():
            return False

        self.blockchain._chain.append(block)
        reward = self.blockchain.get_block_reward(block.header.height)
        self.blockchain._total_minted += reward
        print(f"Block accepted #{block.header.height} {block.hash[:16]}...")
        return True

    def _deserialize_block(self, data: dict) -> Block | None:
        try:
            h = data["header"]
            header = BlockHeader(
                version=h["version"],
                height=h["height"],
                previous_hash=h["previous_hash"],
                merkle_root=h["merkle_root"],
                timestamp=h["timestamp"],
                difficulty=h["difficulty"],
                nonce=h["nonce"],
            )
            txs = [
                self._deserialize_transaction(tx)
                for tx in data.get("transactions", [])
                if tx
            ]
            return Block(
                header=header,
                transactions=[t for t in txs if t],
                hash=data["hash"],
            )
        except Exception as e:
            print(f"Block deserialize error: {e}")
            return None

    def _deserialize_transaction(self, data: dict) -> Transaction | None:
        try:
            inputs = [
                TxInput(
                    tx_id=i["tx_id"],
                    output_index=i["output_index"],
                    signature=i.get("signature", ""),
                )
                for i in data.get("inputs", [])
            ]
            outputs = [
                TxOutput(
                    amount=o["amount"],
                    address=o["address"],
                )
                for o in data.get("outputs", [])
            ]
            return Transaction(
                inputs=inputs,
                outputs=outputs,
                tx_id=data["tx_id"],
                timestamp=data["timestamp"],
                fee=data.get("fee", 0.0),
            )
        except Exception as e:
            print(f"TX deserialize error: {e}")
            return None

    @property
    def peer_count(self) -> int:
        return len(self._peers)

    @property
    def connected_peers(self) -> list[Peer]:
        return [p for p in self._peers.values() if p.is_connected]
