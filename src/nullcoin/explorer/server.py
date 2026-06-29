from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from ..chain.blockchain import Blockchain
from ..chain.block import Block, BlockHeader
from ..chain.transaction import Transaction, TxInput, TxOutput
from .renderer import ExplorerRenderer


def _load_chain(chain_path: str) -> Blockchain | None:
    if not os.path.exists(chain_path):
        return None

    chain = Blockchain()

    with open(chain_path) as f:
        data = json.load(f)

    for b_data in data["chain"]:
        h = b_data["header"]
        header = BlockHeader(
            version=h["version"],
            height=h["height"],
            previous_hash=h["previous_hash"],
            merkle_root=h["merkle_root"],
            timestamp=h["timestamp"],
            difficulty=h["difficulty"],
            nonce=h["nonce"],
        )
        txs = []
        for tx_data in b_data["transactions"]:
            inputs = [
                TxInput(
                    tx_id=i["tx_id"],
                    output_index=i["output_index"],
                    signature=i.get("signature", ""),
                )
                for i in tx_data["inputs"]
            ]
            outputs = [
                TxOutput(
                    amount=o["amount"],
                    address=o["address"],
                )
                for o in tx_data["outputs"]
            ]
            tx = Transaction(
                inputs=inputs,
                outputs=outputs,
                tx_id=tx_data["tx_id"],
                timestamp=tx_data["timestamp"],
                fee=tx_data.get("fee", 0.0),
                memo=tx_data.get("memo", ""),
            )
            txs.append(tx)

        block = Block(
            header=header,
            transactions=txs,
            hash=b_data["hash"],
        )
        chain._chain.append(block)

    chain._difficulty = data.get("difficulty", 4)
    chain._total_minted = data.get("total_minted", 0.0)
    return chain


class ExplorerHandler(BaseHTTPRequestHandler):

    chain_path = ".nullcoin/chain.json"
    renderer = ExplorerRenderer()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        blockchain = _load_chain(self.chain_path)
        if blockchain is None:
            self._respond(500, "No blockchain found.")
            return

        if path == "/" or path == "":
            html = self.renderer.render_index(blockchain)
            self._respond(200, html)

        elif path.startswith("/block/"):
            try:
                height = int(path.split("/block/")[1])
                html = self.renderer.render_block(blockchain, height)
                self._respond(200, html)
            except (ValueError, IndexError):
                self._respond(404, self.renderer._error("Invalid block"))

        elif path.startswith("/address/"):
            address = path.split("/address/")[1]
            html = self.renderer.render_address(blockchain, address)
            self._respond(200, html)

        else:
            self._respond(404, self.renderer._error("Page not found"))

    def _respond(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args) -> None:
        pass


def run_explorer(
    host: str = "0.0.0.0",
    port: int = 8080,
    chain_path: str = ".nullcoin/chain.json",
) -> None:
    ExplorerHandler.chain_path = chain_path
    server = HTTPServer((host, port), ExplorerHandler)
    print(f"NullCoin Explorer running at http://{host}:{port}")
    print(f"Open in browser: http://localhost:{port}")
    print("Press CTRL+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nExplorer stopped.")
