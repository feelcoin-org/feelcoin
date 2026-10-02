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

### Feelcoin v0.1.0 — Linux x64

Download the latest Feelcoin binaries from:

https://github.com/feelcoin-dev/feelcoin/releases/latest

Included binaries:

- `feelcoind`
- `feelcoin-wallet-cli`
- `feelcoin-wallet-rpc`

A SHA-256 checksum file is provided with the release.

Always verify the checksum before running downloaded binaries.

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

- The official Feelcoin mining pool
- Compatible RandomX mining software
- The built-in Feelcoin daemon miner

Official mining pool repository:

https://github.com/feelcoin-dev/feelcoin-pool

---

## Built-in Solo Mining

The Feelcoin daemon includes a built-in miner.

Example:

```text
start_mining YOUR_FEELCOIN_ADDRESS 1
```

The final value specifies the number of CPU mining threads.

Example using four threads:

```text
start_mining YOUR_FEELCOIN_ADDRESS 4
```

Mining status can be checked with:

```text
mining_status
```

Mining can be stopped with:

```text
stop_mining
```

---

## Build From Source

Feelcoin is derived from the Monero codebase.

Clone the repository:

```bash
git clone https://github.com/feelcoin-dev/feelcoin.git
cd feelcoin
```

Build:

```bash
make release
```

The exact build directory may vary depending on platform and build configuration.

---

## Release Verification

Feelcoin binary releases include SHA-256 checksums.

Example:

```bash
sha256sum feelcoin-v0.1.0-linux-x64.tar.gz
```

Compare the resulting hash with the provided:

```text
feelcoin-v0.1.0-linux-x64.tar.gz.sha256
```

Do not run downloaded binaries if the checksum does not match.

---

## Wallet Security

Never share:

- Recovery seeds
- Private spend keys
- Wallet password files
- Private wallet files
- Private RPC credentials

Anyone who obtains your recovery seed or private spend key can control the funds stored in the wallet.

Always keep secure backups of important wallet information.

---

## Paper Wallet Security

The Feelcoin paper wallet generator can create printable wallet recovery information.

Paper wallets should be stored securely and privately.

Anyone who obtains the printed recovery seed or private spend key can access the wallet.

For high-security storage, offline wallet generation is recommended.

---

## Development Status

Feelcoin is currently in early public development.

Components may continue to evolve, including:

- Core software
- Network configuration
- Mining infrastructure
- Wallet tooling
- Block explorer
- Pool software
- Documentation

Users should verify release notes and checksums when upgrading.

---

## Official Repositories

### Core

https://github.com/feelcoin-dev/feelcoin

### Mining Pool

https://github.com/feelcoin-dev/feelcoin-pool

### Block Explorer

https://github.com/feelcoin-dev/feelcoin-explorer

### Paper Wallet

https://github.com/feelcoin-dev/feelcoin-paper-wallet

---

## Current Release

```text
Feelcoin v0.1.0
```

Platform currently published:

```text
Linux x64
```

Windows builds may be published in future releases.

---

## License

Feelcoin is derived from open-source Monero technology.

Applicable upstream licenses and licenses of incorporated open-source components remain applicable.

See the repository licensing files for details.

---

# Feelcoin

## In Feels We Trust
