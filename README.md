# NullCoin (NLC)

> *Privacy is not a feature. It is the foundation.*

NullCoin is a privacy-first blockchain where every transaction
is private by default, yet the total supply remains publicly
verifiable — a property no existing privacy coin achieves.

---

## Why NullCoin?

| Property | Bitcoin | Monero | Zcash | **NullCoin** |
|---|---|---|---|---|
| Privacy by default | ✗ | ✓ | ✗ | **✓** |
| Verifiable supply | ✓ | ✗ | ✓ | **✓** |
| True fungibility | ✗ | ✓ | ✗ | **✓** |
| No trusted setup | ✓ | ✓ | ✗ | **✓** |
| Lightweight node | ✗ | ✗ | ✗ | **✓** |

---

## Quick Start

\```bash
pip install nullcoin
\```

\```bash
nullcoin wallet create miner
nullcoin chain init miner
nullcoin mine --wallet miner
nullcoin wallet balance miner
\```

---

## How It Works

NullCoin uses **Pedersen Commitments** to hide transaction
amounts while preserving mathematical verifiability:

\```
C = r·G + v·H
\```

- `v` = amount (hidden from everyone except sender/receiver)
- `r` = random blinding factor
- `G`, `H` = elliptic curve generator points

The network verifies that inputs equal outputs without
knowing any amounts:

\```
C(input) = C(output) + C(fee)
\```

Coinbase transactions use blinding factor zero, allowing
anyone to verify total supply without seeing any
individual transaction.

---

## Features

- **Mandatory privacy** — no transparent mode, ever
- **Verifiable supply** — 18,000,000 NLC maximum, auditable
- **Fair launch** — no premine, no founder reward
- **Proof of Work** — SHA256, 60-second block time
- **Tail emission** — 0.1 NLC per block after all halvings
- **ECDSA** — secp256k1, same curve as Bitcoin
- **Lightweight** — runs on Raspberry Pi, Android (Termux)

---

## Emission Schedule

\```
Blocks 0–209,999       →  6.0 NLC per block
Blocks 210,000–419,999 →  3.0 NLC per block
Blocks 420,000–629,999 →  1.5 NLC per block
...
After 64 halvings      →  0.1 NLC per block (forever)

Total supply: 18,000,000 NLC
\```

---

## CLI Reference

\```bash
nullcoin wallet create [name]     # Create new wallet
nullcoin wallet info [name]       # Show wallet info
nullcoin wallet balance [name]    # Check balance
nullcoin wallet list              # List all wallets
nullcoin chain init [wallet]      # Initialize blockchain
nullcoin chain info               # Show chain status
nullcoin chain validate           # Validate chain integrity
nullcoin mine [--wallet name]     # Mine a block
nullcoin send <address> <amount>  # Send NLC
nullcoin version                  # Show version
\```

---

## Architecture

\```
src/nullcoin/
├── chain/
│   ├── block.py          # Block and BlockHeader
│   ├── blockchain.py     # Chain validation, UTXO tracking
│   ├── constants.py      # Supply, timing, difficulty
│   ├── miner.py          # Proof of Work
│   └── transaction.py    # Transaction model
├── crypto/
│   ├── keys.py           # ECDSA private/public keys
│   ├── pedersen.py       # Pedersen Commitments
│   └── private_tx.py     # Private transaction engine
├── wallet/
│   └── wallet.py         # Wallet, UTXO, signing
└── cli/
    └── main.py           # Command line interface
\```

---

## Roadmap

- [x] Phase 1 — Core Blockchain
- [x] Phase 2 — Wallet System
- [x] Phase 3 — Privacy Layer (Pedersen Commitments)
- [x] Phase 4 — CLI Interface
- [ ] Phase 5 — P2P Network
- [ ] Phase 6 — Block Explorer
- [ ] Phase 7 — GUI Wallet
- [ ] Phase 8 — Mainnet Launch

---

## Whitepaper

Read the full technical whitepaper: [WHITEPAPER.md](WHITEPAPER.md)

---

## Contributing

NullCoin is built in public. All contributions welcome.

\```bash
git clone https://github.com/painhub-ui/nullcoin
cd nullcoin
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/
\```

---

## Support

If NullCoin helped you, consider supporting development:

**Bitcoin:** `bc1qkuyjev0prea2k3vs0uwlr4h0gzww2y7l0qt4dh`

---

## Disclaimer

NullCoin is experimental software under active development.
Use at your own risk. This is not financial advice.

---

*The code is the law. The math is the proof. The network is the bank.*
