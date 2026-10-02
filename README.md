<p align="center">
  <img src="https://i.imgur.com/VPorAY4.jpeg" alt="Feelcoin Logo" width="180">
</p>

<h1 align="center">Feelcoin</h1>

<p align="center">
  Independent RandomX Proof-of-Work cryptocurrency.
</p>

<p align="center">
  <strong>In Feels We Trust</strong>
</p>

---

## Overview

Feelcoin is an independent cryptocurrency project built from the Monero codebase and adapted into its own network, branding, configuration, ports, data paths, services, mining pool, and block explorer.

Feelcoin uses the RandomX Proof-of-Work algorithm and is designed for CPU-friendly mining.

This repository contains the core Feelcoin blockchain software, including the daemon, wallet components, RPC services, consensus configuration, networking code, blockchain utilities, and supporting libraries.

---

## Project Status

Feelcoin is currently in early public development and testing.

Current public version identity:

`Feelcoin v0.1.0`

Current network type:

`mainnet`

Project motto:

> **In Feels We Trust**

---

## Core Features

- RandomX Proof-of-Work
- CPU-friendly mining
- Independent Feelcoin network identity
- Feelcoin-specific ports
- Feelcoin-specific data directory
- Feelcoin daemon
- Wallet support
- Daemon JSON-RPC
- Wallet RPC support
- Mining pool support
- Block explorer support
- P2P networking
- LMDB blockchain storage
- Monero-derived privacy architecture
- Open-source development

---

## Feelcoin Ecosystem

### Feelcoin Core

Repository:

`https://github.com/feelcoin-dev/feelcoin`

### Feelcoin Mining Pool

Repository:

`https://github.com/feelcoin-dev/feelcoin-pool`

Mining endpoint:

`162.35.27.43:4242`

Pool dashboard:

`http://162.35.27.43:4243`

### Feelcoin Block Explorer

Repository:

`https://github.com/feelcoin-dev/feelcoin-explorer`

Explorer:

`http://162.35.27.43:8081`

---

## Network Services

Current Feelcoin service ports:

| Service | Port |
|---|---:|
| Feelcoin Daemon RPC | `35781` |
| Feelcoin Wallet RPC | `35784` |
| Mining Pool | `4242` |
| Pool Dashboard | `4243` |
| Block Explorer | `8081` |

The daemon RPC and wallet RPC should normally remain bound to localhost unless explicitly configured otherwise.

---

## Data Directory

The default Feelcoin blockchain data directory is:

`~/.feelcoin/`

The LMDB blockchain database is stored under:

`~/.feelcoin/lmdb/`

---

## Build

Feelcoin is built using CMake and the standard project build system.

From the repository root:

```bash
cd /home/feeladmin/feelcoin
```

Create or use the configured build tree and compile the project.

The current release build tree used by this deployment is:

```text
build/Linux/feelcoin-main/release
```

Core binaries are produced under:

```text
build/Linux/feelcoin-main/release/bin/
```

---

## Feelcoin Daemon

The Feelcoin daemon binary is:

```text
build/Linux/feelcoin-main/release/bin/feelcoind
```

Run manually:

```bash
cd /home/feeladmin/feelcoin

./build/Linux/feelcoin-main/release/bin/feelcoind
```

For non-interactive/server use:

```bash
./build/Linux/feelcoin-main/release/bin/feelcoind --non-interactive
```

The non-interactive option is recommended when running under systemd.

---

## Daemon RPC

The Feelcoin daemon RPC endpoint used by the current deployment is:

`127.0.0.1:35781`

Example network information request:

```bash
curl -s http://127.0.0.1:35781/get_info
```

Example JSON-RPC request:

```bash
curl -s http://127.0.0.1:35781/json_rpc   -H 'Content-Type: application/json'   -d '{"jsonrpc":"2.0","id":"0","method":"get_block_count"}'
```

The RPC interface is used by the mining pool and block explorer.

---

## Wallet RPC

The current Feelcoin wallet RPC port is:

`35784`

The mining pool is configured to communicate with wallet RPC through:

```text
127.0.0.1:35784
```

For security, wallet RPC should not be exposed directly to the public internet.

---

## Mining

Feelcoin uses RandomX Proof-of-Work.

The current public mining pool endpoint is:

`162.35.27.43:4242`

Example XMRig command:

```bash
xmrig -o 162.35.27.43:4242   -u YOUR_FEELCOIN_WALLET_ADDRESS   -p x
```

Replace `YOUR_FEELCOIN_WALLET_ADDRESS` with a valid Feelcoin wallet address.

For full pool instructions, see:

`https://github.com/feelcoin-dev/feelcoin-pool`

---

## Mining Pool

The Feelcoin mining pool currently provides:

- RandomX mining
- PPLNS reward accounting
- dynamic difficulty
- miner statistics
- pool statistics
- web dashboard
- miner lookup
- block explorer integration
- configurable pool fee
- configurable payout threshold

Pool dashboard:

`http://162.35.27.43:4243`

---

## Block Explorer

The Feelcoin block explorer connects directly to the local `feelcoind` RPC service.

It currently provides:

- blockchain height
- network difficulty
- estimated network hashrate
- latest blocks
- block height search
- block hash search
- transaction hash search
- mempool statistics
- network connection information

Explorer:

`http://162.35.27.43:8081`

Repository:

`https://github.com/feelcoin-dev/feelcoin-explorer`

---

## Automatic Service Startup

The current server deployment uses systemd to manage:

- `feelcoind`
- `feelcoin-pool`
- `feelcoin-explorer`

Example daemon service:

```ini
[Unit]
Description=Feelcoin Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=feeladmin
WorkingDirectory=/home/feeladmin/feelcoin
ExecStart=/home/feeladmin/feelcoin/build/Linux/feelcoin-main/release/bin/feelcoind --non-interactive
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable feelcoind
```

Start:

```bash
sudo systemctl start feelcoind
```

Check status:

```bash
sudo systemctl status feelcoind
```

---

## Health Checks

Check the daemon RPC:

```bash
sudo ss -lntp | grep 35781
```

Check all Feelcoin services:

```bash
sudo systemctl is-active feelcoind feelcoin-pool feelcoin-explorer
```

Check currently used service ports:

```bash
sudo ss -lntp | grep -E '35781|4242|4243|8081'
```

A healthy deployment should show:

```text
feelcoind           active
feelcoin-pool       active
feelcoin-explorer   active
```

---

## Repository Structure

The project is based on the Monero source tree, with Feelcoin-specific changes across core blockchain, networking, RPC, wallet, configuration, and utility components.

Important modified areas include:

```text
src/blockchain_utilities/
src/checkpoints/
src/cryptonote_basic/
src/cryptonote_core/
src/p2p/
src/rpc/
src/wallet/
```

Feelcoin-specific blockchain utility source:

```text
src/blockchain_utilities/feelcoin_genesis.cpp
```

---

## Development

The primary Feelcoin development branch is:

`main`

The project preserves an upstream Monero remote for reference and future source review.

Recommended Git remote structure:

```text
origin    git@github.com:feelcoin-dev/feelcoin.git
upstream  https://github.com/monero-project/monero.git
```

This allows Feelcoin development to remain independent while still making upstream comparison and maintenance possible.

---

## Security

For production deployments:

- keep daemon RPC private unless public access is intentionally required
- keep wallet RPC private
- never publish wallet seeds or private keys
- never commit wallet files containing secrets
- never commit production credentials
- use firewall rules
- use HTTPS for public websites
- use TLS for public mining endpoints when available
- keep the operating system and dependencies updated
- monitor daemon, pool, and explorer logs
- back up important wallet and configuration data securely

---

## Related Repositories

### Core

`https://github.com/feelcoin-dev/feelcoin`

### Mining Pool

`https://github.com/feelcoin-dev/feelcoin-pool`

### Block Explorer

`https://github.com/feelcoin-dev/feelcoin-explorer`

---

## Branding

<p align="center">
  <img src="https://i.imgur.com/VPorAY4.jpeg" alt="Feelcoin" width="130">
</p>

<p align="center">
  <strong>Feelcoin</strong>
</p>

<p align="center">
  <strong>In Feels We Trust</strong>
</p>

---

## Upstream Attribution

Feelcoin is derived from the open-source Monero project and has been modified to operate as an independent network.

Original upstream repository:

`https://github.com/monero-project/monero`

Feelcoin retains upstream attribution and licensing obligations where applicable.

The Monero project and its contributors are not responsible for, affiliated with, or endorsing Feelcoin unless explicitly stated otherwise.

---

## License

See the repository `LICENSE` file for licensing information and applicable upstream notices.

---

<p align="center">
  <strong>Feelcoin Network</strong>
</p>

<p align="center">
  <strong>In Feels We Trust</strong>
</p>
