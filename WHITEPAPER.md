# NullCoin: A Privacy-First Blockchain with Verifiable Supply

**NullCoin Development Team**
Contact: nullcoin@proton.me *(to be created)*
Version: 0.1 Draft
Date: 2026

---

## Abstract

We propose NullCoin (NLC), a decentralized cryptocurrency
that solves the fundamental tension between privacy and
verifiability in existing blockchain systems. Current
privacy coins either hide transaction amounts without
allowing supply verification (Monero), or offer privacy
as an optional feature that weakens the anonymity set
(Zcash). NullCoin implements mandatory privacy using
Pedersen Commitments, ensuring all transaction amounts
are hidden by default while allowing anyone to
cryptographically verify that the total supply has
not been inflated. Combined with a fair Proof of Work
consensus, tail emission for long-term security, and
a lightweight node design that runs on consumer hardware,
NullCoin aims to be the foundation for genuinely private
and sovereign financial transactions.

---

## 1. Introduction

The promise of cryptocurrency was financial sovereignty —
the ability to transact freely without the permission
or surveillance of any third party. In practice, most
cryptocurrencies have failed to deliver this promise.

Bitcoin transactions are fully transparent. Every
payment, every balance, every transaction history is
permanently recorded on a public ledger that anyone
can analyze. Chain analysis firms routinely de-anonymize
Bitcoin users, and governments increasingly require
exchanges to report transaction histories.

Privacy coins like Monero offer stronger anonymity but
introduce a different problem: the total supply cannot
be independently verified. Users must trust that the
cryptographic implementation contains no bugs that
would allow silent inflation. This trust requirement
undermines the "verify, don't trust" principle that
makes cryptocurrency valuable.

NullCoin resolves this tension. Every transaction is
private by default. No one can see how much you sent,
to whom, or what your balance is. Yet anyone can
verify that the total supply of NullCoin has not
been inflated — without seeing any individual
transaction. This is not a theoretical improvement.
It is a fundamental advance in the design of
private money.

---

## 2. Problems with Existing Systems

### 2.1 Bitcoin: Transparent by Default

Bitcoin's UTXO model records all transactions
permanently on a public ledger. While addresses
are pseudonymous, they are trivially linkable through
chain analysis. The fungibility of Bitcoin is
compromised — coins with histories associated with
illegal activity are blacklisted by exchanges,
meaning not all bitcoins are equal.

### 2.2 Monero: Private but Unverifiable

Monero uses Ring Signatures, Stealth Addresses, and
RingCT to hide sender, receiver, and amount. However,
the total supply cannot be independently audited.
A bug in the RingCT implementation — as nearly
occurred in 2017 — could allow an attacker to
create coins from nothing, with no one able to
detect the inflation.

### 2.3 Zcash: Optional Privacy

Zcash implements zk-SNARKs for strong privacy but
makes it optional. In practice, over 85% of Zcash
transactions use the transparent pool, severely
weakening the anonymity set. Optional privacy is
effectively no privacy.

### 2.4 The Common Problem

No existing system provides all four properties
simultaneously.

---

## 3. NullCoin Design

### 3.1 Core Principles

**Privacy is not a feature. It is the foundation.**

Every design decision in NullCoin flows from this
principle. There is no transparent mode. There is
no optional privacy. All transactions are private,
or none are.

**Verify, don't trust.**

Users should never need to trust the NullCoin
development team, any exchange, or any third party.
Every claim the protocol makes — including the
total supply — must be independently verifiable
by any participant.

**Sovereignty requires accessibility.**

A privacy coin that requires specialized hardware
to run a node is not truly decentralized. NullCoin
is designed to run on consumer hardware, including
mobile devices, ensuring broad participation.

### 3.2 Transaction Model

NullCoin uses a commitment-based UTXO model.
Instead of recording amounts in plaintext, each
output contains a Pedersen Commitment.

Where:
- `v` is the transaction amount (hidden)
- `r` is a random blinding factor (known only to sender/receiver)
- `G` is the standard elliptic curve generator point
- `H` is a second generator point derived from G via
  hash-to-curve, ensuring no one knows the discrete
  logarithm relationship between G and H

This construction allows verification that inputs
equal outputs without revealing any amounts.

If the blinding factors are balanced, this equation
holds if and only if v_in = v_out + v_fee.

### 3.3 Verifiable Supply

The total supply of NullCoin can be verified as follows:

All coinbase transactions (block rewards) use a
blinding factor of zero and an amount equal to the
block reward. This means coinbase commitments are
publicly known values. By summing all coinbase
commitments and verifying they equal the sum of
all UTXO commitments in the system, any participant
can verify the total supply without seeing any
individual transaction amount.

This is NullCoin's fundamental advance over Monero:
supply auditability without sacrificing transaction
privacy.

### 3.4 Address System

NullCoin uses ECDSA on the secp256k1 curve for key
generation, consistent with Bitcoin. Addresses are
derived as follows.

All NullCoin addresses begin with the prefix "NLC",
providing immediate visual identification.

### 3.5 Consensus: Proof of Work

NullCoin uses SHA256-based Proof of Work with
difficulty adjustment every 2,016 blocks, targeting
a 60-second block time. This is consistent with
Bitcoin's proven security model while reducing
transaction confirmation times.

**Why not Proof of Stake?**

Proof of Stake systematically advantages those with
existing wealth. Large stakeholders earn
proportionally more, compounding their advantage
over time. NullCoin's mission is financial
sovereignty for all — not a system that further
concentrates wealth.

### 3.6 Emission Schedule
Block Height    Reward per Block
0 - 209,999     6.0 NLC
210,000-419,999 3.0 NLC
420,000-629,999 1.5 NLC
...
After 64 halvings: 0.1 NLC (tail emission)

**Total Supply: 18,000,000 NLC**

The tail emission of 0.1 NLC per block continues
indefinitely, ensuring miners always have an
incentive to secure the network — addressing
Bitcoin's long-term security budget problem.

---

## 4. Security Analysis

### 4.1 Commitment Binding

The security of Pedersen Commitments relies on the
hardness of the discrete logarithm problem on
secp256k1. An adversary who could compute discrete
logarithms could create commitments that appear
balanced but hide inflation. This is the same
assumption underlying Bitcoin's signature security.

### 4.2 51% Attack Resistance

As with all Proof of Work systems, an attacker
controlling 51% of the network hashrate could
rewrite recent blocks. NullCoin mitigates this
through the same mechanisms as Bitcoin: the
cumulative proof of work makes deep reorganizations
prohibitively expensive.

### 4.3 Privacy Guarantees

Transaction privacy in NullCoin is unconditional
given the hardness of the discrete logarithm problem.
Unlike Zcash's zk-SNARKs, which require a trusted
setup ceremony, NullCoin's Pedersen Commitments
require no trusted setup.

---

## 5. Comparison with Related Work

### 5.1 vs Bitcoin

NullCoin inherits Bitcoin's UTXO model and Proof
of Work security while adding mandatory transaction
privacy. Unlike Bitcoin, all NullCoin transactions
hide amounts and improve fungibility.

### 5.2 vs Monero

NullCoin and Monero share the goal of mandatory
privacy. NullCoin's key advance is verifiable supply
through structured coinbase commitments, addressing
Monero's primary weakness.

### 5.3 vs Zcash

NullCoin achieves stronger privacy guarantees than
Zcash without a trusted setup ceremony and with
mandatory (not optional) privacy for all
transactions.

---

## 6. Roadmap

### Phase 1 — Core Protocol (Complete)
- Block structure and chain validation
- Proof of Work mining
- Transaction model with UTXO tracking
- Block reward and halving schedule

### Phase 2 — Cryptographic Wallet (Complete)
- ECDSA key generation on secp256k1
- NLC address derivation
- Transaction signing and verification
- UTXO selection and change handling

### Phase 3 — Privacy Layer (Complete)
- Pedersen Commitment implementation
- Private transaction construction
- Commitment sum verification
- Range proof foundation

### Phase 4 — Command Line Interface (Complete)
- Wallet management
- Chain initialization and mining
- Transaction creation and broadcast
- Chain validation

### Phase 5 — P2P Network (In Progress)
- Node discovery
- Block propagation
- Transaction mempool
- Chain synchronization

### Phase 6 — Ecosystem
- Block explorer
- GUI wallet
- Mobile node support
- Exchange integration

---

## 7. Fair Launch

NullCoin will launch with no premine, no founder
reward, and no investor allocation. The genesis
block reward goes to the first public miner.
All NLC in existence will have been earned through
Proof of Work.

The NullCoin development team will mine using the
same software and hardware available to the public,
beginning at the same time as all other participants.

This is not a promise. It is enforced by the
protocol itself.

---

## 8. Conclusion

NullCoin represents a step forward in the design
of private money. By combining mandatory Pedersen
Commitment-based privacy with a verifiable supply
mechanism, NullCoin resolves the fundamental tension
that has existed in privacy cryptocurrency since
Monero's launch in 2014.

We release this implementation and this paper
without reservation, to be examined, critiqued,
improved, and extended by anyone who finds value
in genuinely private, sovereign money.

The code is the law.
The math is the proof.
The network is the bank.

---

## References

1. Nakamoto, S. (2008). Bitcoin: A Peer-to-Peer
   Electronic Cash System.

2. Noether, S. (2015). Ring Signature Confidential
   Transactions for Monero.

3. Ben-Sasson, E. et al. (2014). Zerocash:
   Decentralized Anonymous Payments from Bitcoin.

4. Pedersen, T. (1991). Non-Interactive and
   Information-Theoretic Secure Verifiable Secret
   Sharing.

5. Maxwell, G. (2015). Confidential Transactions.

---

*NullCoin is experimental software. Use at your
own risk. This is not financial advice.*

*"Privacy is not something that I'm merely entitled
to, it's an absolute prerequisite."*
— Marlon Brando


