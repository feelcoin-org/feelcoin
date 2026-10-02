# Feelcoin

![Feelcoin Logo](https://i.imgur.com/VPorAY4.jpeg)

## In Feels We Trust

Feelcoin is an independent RandomX Proof-of-Work cryptocurrency derived from Monero technology.

The Feelcoin ecosystem includes:

- Core node software
- CLI wallet
- Wallet RPC
- Mining pool
- Block explorer
- Paper wallet generator

---

## Latest Release

### Feelcoin v0.2.0 — Linux x64 / Windows x64

Download the latest Feelcoin binaries from:

https://github.com/feelcoin-dev/feelcoin/releases/latest

Included core binaries:

- `feelcoind`
- `feelcoin-wallet-cli`
- `feelcoin-wallet-rpc`

SHA-256 checksum files should be provided with release assets.

Always verify checksums before running downloaded binaries.

---

## Feelcoin Ecosystem

### Feelcoin Core

Main Feelcoin node and wallet implementation.

Repository:

https://github.com/feelcoin-dev/feelcoin

---

### Feelcoin Mining Pool

Official RandomX mining pool for the Feelcoin network.

Repository:

https://github.com/feelcoin-dev/feelcoin-pool

The pool provides:

- RandomX mining
- Live pool statistics
- Miner tracking
- PPLNS reward accounting
- Automatic payout support
- Feelcoin block explorer integration

Current official pool fee:

```text
0.5%
```

This is a pool service fee and is separate from the protocol-level development treasury.

---

### Feelcoin Block Explorer

Official Feelcoin blockchain explorer.

Repository:

https://github.com/feelcoin-dev/feelcoin-explorer

The explorer provides:

- Blockchain height
- Network statistics
- Latest blocks
- Block lookup
- Transaction lookup
- Block reward information
- Hash search

Explorer fee:

```text
0%
```

---

### Feelcoin Paper Wallet

Official Feelcoin paper wallet generator.

Repository:

https://github.com/feelcoin-dev/feelcoin-paper-wallet

Features include:

- Genuine Feelcoin wallet generation
- Feelcoin public address
- 25-word recovery seed
- Private spend key
- Private view key
- Public address QR code
- Printable paper wallet
- PDF export

Paper wallet fee:

```text
0%
```

---

## Network Information

| Parameter | Value |
|---|---|
| Network | Feelcoin Mainnet |
| Consensus | Proof of Work |
| Mining Algorithm | RandomX |
| Block Target | 120 seconds |
| Decimal Places | 12 |
| Standard Address Prefix | 84 |
| Integrated Address Prefix | 85 |
| Subaddress Prefix | 86 |

### Monetary Units

Feelcoin uses 12 decimal places.

```text
1 FEEL = 1,000,000,000,000 atomic units
```

---

## Block Reward & Development Treasury

Starting from **block 590**, Feelcoin uses a consensus-enforced development treasury.

For every block subsidy:

| Allocation | Amount |
|---|---:|
| Miner / Pool | 98% |
| Feelcoin Development Treasury | 2% |

Transaction fees are **not** subject to the development allocation.

```text
Block subsidy:
98% -> miner / pool
 2% -> Feelcoin development treasury

Transaction fees:
100% -> miner / pool
```

### Development Treasury Address

```text
FBXZD77V6Rac7o7Ukc16j8g6iPpu6LuV5Udi3UMgopATBGrbycUSTmXUQcm1B2bx8HMYyjZHxoEtqUokaUweUvWKMEbnBkc
```

The treasury rule is enforced by Feelcoin consensus. Blocks created at or after height 590 must contain the required treasury output.

The treasury allocation does **not** create additional inflation. It is deducted from the existing block subsidy.

### Fee Summary

| Fee / Allocation | Amount | Destination |
|---|---:|---|
| Development Treasury | 2% of block subsidy | Feelcoin development treasury |
| Miner / Pool Subsidy | 98% of block subsidy | Block miner / pool |
| Transaction Fees | 100% | Block miner / pool |
| Official Pool Fee | 0.5% | Pool operation / infrastructure |
| Solo Mining Pool Fee | 0% | — |
| Block Explorer Fee | 0% | — |
| Paper Wallet Fee | 0% | — |

---

## Quick Start

### Start the Feelcoin daemon

```bash
./feelcoind
```

The daemon downloads, validates, and maintains the Feelcoin blockchain.

### Create or open a wallet

```bash
./feelcoin-wallet-cli
```

The wallet CLI can be used to:

- Create wallets
- Restore wallets from seed
- View balances
- Generate addresses
- Send FEEL
- Receive FEEL

### Wallet RPC

For applications and services:

```bash
./feelcoin-wallet-rpc --help
```

The wallet RPC is used by services such as mining pools and wallet applications.

For security, wallet RPC services should normally remain bound to localhost unless properly secured.

---

## Mining

Feelcoin uses the RandomX Proof-of-Work algorithm.

RandomX is designed primarily for general-purpose CPUs.

Mining can be performed through:

- Solo mining
- Official Feelcoin pool
- Compatible third-party RandomX mining software

### Solo Mining

Start the daemon and use:

```text
start_mining <FEEL_ADDRESS> <THREADS>
```

Check mining status:

```text
mining_status
```

Stop mining:

```text
stop_mining
```

Solo miners do not pay the official pool fee. The protocol-level 2% development treasury still applies from block 590 onward.

---

## Security

- Never share wallet seeds.
- Never share private spend keys.
- Keep wallet RPC bound to localhost unless it is properly authenticated and firewalled.
- Verify release checksums.
- Back up wallet seeds offline.
- Treat any wallet credentials exposed publicly as compromised.

---

## Open Source Lineage

Feelcoin is derived from the Monero open-source codebase and inherits battle-tested cryptographic, networking, wallet, and RandomX foundations.

Feelcoin is not presented as a clean-room implementation of those technologies.

Feelcoin operates as an independent blockchain with its own:

- Genesis
- Network identity
- Address namespace
- Chain history
- Infrastructure
- Releases
- Development direction
- Consensus-enforced development treasury

---

## Development Status

Feelcoin is under active development.

Current ecosystem components include:

- Core node
- CLI wallet
- Wallet RPC
- Mining pool
- Block explorer
- Paper wallet
- Linux release
- Windows release in preparation
- Consensus-enforced 2% development treasury

---

## In Feels We Trust
