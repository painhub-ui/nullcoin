from __future__ import annotations

import json
import os
import sys


def main() -> None:
    args = sys.argv[1:]

    if not args:
        _print_help()
        return

    command = args[0]
    sub = args[1] if len(args) > 1 else ""

    if command == "wallet":
        _cmd_wallet(sub, args[2:])
    elif command == "chain":
        _cmd_chain(sub, args[2:])
    elif command == "mine":
        _cmd_mine(args[1:])
    elif command == "send":
        _cmd_send(args[1:])
    elif command == "explorer":
        _cmd_explorer(args[1:])
    elif command == "version":
        _cmd_version()
    else:
        print(f"Unknown command: {command}")
        _print_help()
        print("  nullcoin explorer [--port N]     Launch block explorer")
def _cmd_wallet(sub: str, args: list[str]) -> None:
    if sub == "create":
        _wallet_create(args)
    elif sub == "info":
        _wallet_info(args)
    elif sub == "balance":
        _wallet_balance(args)
    elif sub == "list":
        _wallet_list()
    else:
        print("Usage:")
        print("  nullcoin wallet create [name]")
        print("  nullcoin wallet info [name]")
        print("  nullcoin wallet balance [name]")
        print("  nullcoin wallet list")


def _wallet_create(args: list[str]) -> None:
    from ..wallet import Wallet

    name = args[0] if args else "default"
    path = _wallet_path(name)

    if os.path.exists(path):
        print(f"Wallet already exists: {name}")
        return

    wallet = Wallet()
    os.makedirs(".nullcoin/wallets", exist_ok=True)
    wallet.save(path)

    print()
    print(f"Wallet created: {name}")
    print(f"Address       : {wallet.address}")
    print()
    print("WARNING: Back up your private key!")
    print(f"File: {path}")


def _wallet_info(args: list[str]) -> None:
    from ..wallet import Wallet

    name = args[0] if args else "default"
    path = _wallet_path(name)

    if not os.path.exists(path):
        print(f"Wallet not found: {name}")
        print("Run: nullcoin wallet create")
        return

    wallet = Wallet.load(path)
    print(f"Wallet   : {name}")
    print(f"Address  : {wallet.address}")
    print(f"Pub Key  : {wallet.public_key[:32]}...")


def _wallet_balance(args: list[str]) -> None:
    from ..wallet import Wallet
    from ..chain import Blockchain

    name = args[0] if args else "default"
    path = _wallet_path(name)

    if not os.path.exists(path):
        print(f"Wallet not found: {name}")
        return

    wallet = Wallet.load(path)
    chain = _load_chain()

    if chain is None:
        print("No blockchain found. Run: nullcoin mine --init")
        return

    balance = chain.get_balance(wallet.address)
    print(f"Address : {wallet.address}")
    print(f"Balance : {balance} NLC")


def _wallet_list() -> None:
    wallets_dir = ".nullcoin/wallets"
    if not os.path.exists(wallets_dir):
        print("No wallets found.")
        return

    files = [f for f in os.listdir(wallets_dir) if f.endswith(".json")]
    if not files:
        print("No wallets found.")
        return

    print(f"{'Name':<20} {'Address'}")
    print("-" * 70)
    for f in sorted(files):
        name = f.replace(".json", "")
        path = os.path.join(wallets_dir, f)
        with open(path) as fp:
            data = json.load(fp)
        print(f"{name:<20} {data['address']}")


def _cmd_chain(sub: str, args: list[str]) -> None:
    if sub == "info":
        _chain_info()
    elif sub == "init":
        _chain_init(args)
    elif sub == "validate":
        _chain_validate()
    else:
        print("Usage:")
        print("  nullcoin chain init [wallet]")
        print("  nullcoin chain info")
        print("  nullcoin chain validate")


def _chain_init(args: list[str]) -> None:
    from ..chain import Blockchain
    from ..wallet import Wallet

    chain_path = ".nullcoin/chain.json"
    if os.path.exists(chain_path):
        print("Chain already initialized.")
        return

    name = args[0] if args else "default"
    wallet_path = _wallet_path(name)

    if not os.path.exists(wallet_path):
        print(f"Wallet not found: {name}")
        print("Run: nullcoin wallet create")
        return

    wallet = Wallet.load(wallet_path)

    print(f"Initializing NullCoin chain...")
    print(f"Miner address: {wallet.address}")
    print()

    chain = Blockchain()
    chain.initialize(wallet.address)

    os.makedirs(".nullcoin", exist_ok=True)
    chain.save(chain_path)

    print()
    print(f"Chain initialized!")
    print(f"Genesis block mined.")
    print(f"Reward: {chain.total_minted} NLC → {wallet.address}")


def _chain_info() -> None:
    from ..chain.constants import COIN_NAME, TICKER, TOTAL_SUPPLY

    chain = _load_chain()
    if chain is None:
        print("No chain found. Run: nullcoin chain init")
        return

    print(f"=== {COIN_NAME} ({TICKER}) ===")
    print()
    print(f"Height       : {chain.height}")
    print(f"Difficulty   : {chain._difficulty}")
    print(f"Total minted : {chain.total_minted} NLC")
    print(f"Max supply   : {TOTAL_SUPPLY} NLC")
    print(f"Pending txs  : {chain.pending_count}")
    print(f"Chain valid  : {chain.is_valid_chain()}")

    if chain.last_block:
        b = chain.last_block
        print()
        print(f"Last Block:")
        print(f"  Height   : {b.header.height}")
        print(f"  Hash     : {b.hash[:32]}...")
        print(f"  Txs      : {len(b.transactions)}")


def _chain_validate() -> None:
    chain = _load_chain()
    if chain is None:
        print("No chain found.")
        return

    valid = chain.is_valid_chain()
    print(f"Chain height : {chain.height}")
    print(f"Chain valid  : {valid}")

    if valid:
        print("All blocks verified successfully.")
    else:
        print("WARNING: Chain validation failed!")


def _cmd_mine(args: list[str]) -> None:
    from ..chain import Blockchain
    from ..wallet import Wallet

    name = "default"
    for i, a in enumerate(args):
        if a == "--wallet" and i + 1 < len(args):
            name = args[i + 1]

    wallet_path = _wallet_path(name)
    if not os.path.exists(wallet_path):
        print(f"Wallet not found: {name}")
        print("Run: nullcoin wallet create")
        return

    chain = _load_chain()
    if chain is None:
        print("No chain found. Run: nullcoin chain init")
        return

    wallet = Wallet.load(wallet_path)
    chain_path = ".nullcoin/chain.json"

    print(f"Mining with: {wallet.address}")
    print(f"Pending txs: {chain.pending_count}")
    print()

    block = chain.mine_pending(wallet.address)

    if block:
        chain.save(chain_path)
        reward = chain.get_block_reward(block.header.height)
        print()
        print(f"Block mined!")
        print(f"Height  : {block.header.height}")
        print(f"Hash    : {block.hash[:32]}...")
        print(f"Reward  : {reward} NLC")
        balance = chain.get_balance(wallet.address)
        print(f"Balance : {balance} NLC")
    else:
        print("Mining failed.")


def _cmd_send(args: list[str]) -> None:
    from ..chain import Transaction, TxInput, TxOutput
    from ..wallet import Wallet, UTXO

    if len(args) < 2:
        print("Usage: nullcoin send <recipient> <amount> [--wallet name]")
        return

    recipient = args[0]
    try:
        amount = float(args[1])
    except ValueError:
        print("Invalid amount.")
        return

    name = "default"
    for i, a in enumerate(args):
        if a == "--wallet" and i + 1 < len(args):
            name = args[i + 1]

    wallet_path = _wallet_path(name)
    if not os.path.exists(wallet_path):
        print(f"Wallet not found: {name}")
        return

    chain = _load_chain()
    if chain is None:
        print("No chain found.")
        return

    wallet = Wallet.load(wallet_path)
    balance = chain.get_balance(wallet.address)

    if balance < amount + 0.01:
        print(f"Insufficient balance: {balance} NLC")
        return

    utxos = _get_utxos(chain, wallet.address)
    tx = wallet.create_transaction(
        recipient=recipient,
        amount=amount,
        utxos=utxos,
        fee=0.01,
    )

    if tx is None:
        print("Failed to create transaction.")
        return

    chain.add_transaction(tx)
    chain.save(".nullcoin/chain.json")

    print(f"Transaction created!")
    print(f"TX ID     : {tx.tx_id[:32]}...")
    print(f"From      : {wallet.address}")
    print(f"To        : {recipient}")
    print(f"Amount    : {amount} NLC")
    print(f"Fee       : 0.01 NLC")
    print()
    print("Run 'nullcoin mine' to confirm.")

def _cmd_explorer(args: list[str]) -> None:
    from ..explorer import run_explorer

    port = 8080
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    chain_path = ".nullcoin/chain.json"
    if not os.path.exists(chain_path):
        print("No blockchain found. Run: nullcoin chain init")
        return

    run_explorer(port=port, chain_path=chain_path)

def _cmd_version() -> None:
    from ..chain.constants import COIN_NAME, TICKER, VERSION
    v = ".".join(map(str, VERSION))
    print(f"{COIN_NAME} ({TICKER}) v{v}")


def _print_help() -> None:
    print("NullCoin (NLC) — Privacy-first blockchain")
    print()
    print("Usage:")
    print("  nullcoin wallet create [name]    Create new wallet")
    print("  nullcoin wallet info [name]      Show wallet info")
    print("  nullcoin wallet balance [name]   Show balance")
    print("  nullcoin wallet list             List all wallets")
    print("  nullcoin chain init [wallet]     Initialize blockchain")
    print("  nullcoin chain info              Show chain info")
    print("  nullcoin chain validate          Validate chain")
    print("  nullcoin mine [--wallet name]    Mine a block")
    print("  nullcoin send <addr> <amount>    Send NLC")
    print("  nullcoin version                 Show version")


def _wallet_path(name: str) -> str:
    return f".nullcoin/wallets/{name}.json"

def _load_chain():
    from ..chain import Blockchain
    from ..chain.block import Block, BlockHeader
    from ..chain.transaction import Transaction, TxInput, TxOutput
    import json as _json

    chain_path = ".nullcoin/chain.json"
    if not os.path.exists(chain_path):
        return None

    chain = Blockchain()

    with open(chain_path) as f:
        data = _json.load(f)

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
            )
            txs.append(tx)

        block = Block(header=header, transactions=txs, hash=b_data["hash"])
        chain._chain.append(block)

    chain._difficulty = data.get("difficulty", 4)
    chain._total_minted = data.get("total_minted", 0.0)

    for tx_data in data.get("pending", []):
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
        )
        chain._pending.append(tx)

    return chain


def _get_utxos(chain, address: str):
    from ..wallet import UTXO

    spent = set()
    for block in chain._chain:
        for tx in block.transactions:
            for inp in tx.inputs:
                spent.add((inp.tx_id, inp.output_index))

    utxos = []
    for block in chain._chain:
        for tx in block.transactions:
            for i, out in enumerate(tx.outputs):
                if out.address == address:
                    if (tx.tx_id, i) not in spent:
                        utxos.append(UTXO(
                            tx_id=tx.tx_id,
                            output_index=i,
                            amount=out.amount,
                            address=address,
                        ))
    return utxos
