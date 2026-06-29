from __future__ import annotations

import socket
import threading
import time
from typing import Any, Callable

from .messages import Message, MessageType


class Peer:

    def __init__(
        self,
        host: str,
        port: int,
        on_message: Callable[[Peer, Message], None] | None = None,
        on_disconnect: Callable[[Peer], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self._socket: socket.socket | None = None
        self._connected = False
        self._thread: threading.Thread | None = None
        self.last_seen: float = time.time()
        self.height: int = 0
        self.peer_id: str = f"{host}:{port}"

    @classmethod
    def from_socket(
        cls,
        sock: socket.socket,
        addr: tuple,
        on_message: Callable | None = None,
        on_disconnect: Callable | None = None,
    ) -> Peer:
        peer = cls(
            host=addr[0],
            port=addr[1],
            on_message=on_message,
            on_disconnect=on_disconnect,
        )
        peer._socket = sock
        peer._connected = True
        return peer

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
            )
            self._socket.settimeout(10)
            self._socket.connect((self.host, self.port))
            self._connected = True
            self.last_seen = time.time()
            return True
        except Exception as e:
            print(f"Connect failed {self.peer_id}: {e}")
            self._connected = False
            return False

    def send(self, message: Message) -> bool:
        if not self._connected or self._socket is None:
            return False
        try:
            self._socket.sendall(message.to_bytes())
            return True
        except Exception:
            self._connected = False
            return False

    def start_listening(self) -> None:
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )
        self._thread.start()

    def _listen_loop(self) -> None:
        buffer = b""
        while self._connected:
            try:
                if self._socket is None:
                    break
                self._socket.settimeout(30)
                data = self._socket.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line:
                        try:
                            msg = Message.from_bytes(line)
                            self.last_seen = time.time()
                            if self.on_message:
                                self.on_message(self, msg)
                        except Exception as e:
                            print(f"Parse error from {self.peer_id}: {e}")
            except socket.timeout:
                self.send(Message.ping())
            except Exception:
                break

        self._connected = False
        if self.on_disconnect:
            self.on_disconnect(self)

    def disconnect(self) -> None:
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "height": self.height,
            "last_seen": self.last_seen,
        }
