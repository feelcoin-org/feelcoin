# FEELCOIN
## Exchange & Wallet Integration Guide

**Version 1.0 | 13 October 2026 | Linux / Feelcoin Mainnet**  
**Audience:** Exchange developers, payment processors, custodial wallet operators, and technical integrators  
**Official source:** https://github.com/feelcoin-org/feelcoin  
**Technical support:** support@feelcoin.org

> **Scope and readiness:** This document explains how to build Feelcoin Core, run a local node, connect a wallet RPC service, and design a deposit/withdrawal workflow. It is an integration starting point, **not** a certification of production readiness. Operators must test the exact release, validate custody controls, and approve confirmation and reorganization policies before accepting customer funds.

---

## 1. Network reference

| Item | Feelcoin mainnet |
|---|---|
| Symbol | FEEL |
| Consensus | RandomX Proof of Work |
| Target block time | 120 seconds |
| Decimal precision | 12 places |
| Atomic units | 1 FEEL = 1,000,000,000,000 atomic units |
| Peer-to-peer port | TCP 35780 |
| Local daemon RPC port | TCP 35781 |
| ZMQ RPC port | TCP 35782 |
| Recommended example wallet RPC port | TCP 35784 (operator-selected, not a consensus setting) |
| Mainnet bootstrap peers | node1.feelcoin.org:35780 and node2.feelcoin.org:35780 |
| Core release reviewed | v0.2.1 (official Linux x86_64 stable release at time of writing) |

The mainnet address prefixes and network identity are defined in the core source. **Never substitute a Monero daemon, Monero address, or another network's wallet software for Feelcoin Core.** Feelcoin inherits technology from Monero but operates an independent chain.

The [Feelcoin Public API](https://api.feelcoin.org/docs) supplies **read-only network statistics**. It does **not** create wallets, hold private keys, detect private wallet deposits, sign withdrawals, or replace a local wallet RPC service.

## 2. Prerequisites

Use a **dedicated Linux server** (Ubuntu 22.04/24.04 LTS or another compatible distribution) with a trusted administrator account, sufficient disk space for a growing blockchain, backups, monitoring, and outbound network access. Start in a nonproduction environment with no customer funds.

For Ubuntu, install a baseline set of compiler and library dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
  git build-essential cmake pkg-config \
  libboost-all-dev libssl-dev libzmq3-dev \
  libunbound-dev libminiupnpc-dev libreadline-dev \
  libldns-dev libexpat1-dev libsodium-dev \
  libhidapi-dev libusb-1.0-0-dev \
  libprotobuf-dev protobuf-compiler libudev-dev \
  libcurl4-openssl-dev
```

Dependency availability differs by distribution and release. If CMake reports a missing dependency, install the corresponding `-dev` package and rerun configuration. Avoid copying unreviewed installation scripts from third parties.

## 3. Clone and compile Feelcoin Core from source

Use the **official upstream repository**, including its submodules. For reproducible integration, build a reviewed release tag rather than an arbitrary moving branch:

```bash
git clone --recursive https://github.com/feelcoin-org/feelcoin.git
cd feelcoin

git fetch --tags
git checkout v0.2.1
git submodule update --init --recursive

# Record the exact source revision for your deployment manifest.
git rev-parse HEAD

# Compile the release (limit parallelism if RAM is constrained).
make -j2 release
```

The project's Makefile defines the `release` target; build paths depend on OS, branch, and configuration. Find the resulting programs without assuming a fixed output directory:

```bash
find build -type f \
  \( -name feelcoind -o -name feelcoin-wallet-cli \
     -o -name feelcoin-wallet-rpc \) -print
```

The expected files are:

- `feelcoind` - full node / blockchain daemon.
- `feelcoin-wallet-cli` - interactive wallet creation, recovery, and maintenance.
- `feelcoin-wallet-rpc` - wallet JSON-RPC service for backend applications.

Use `--help` on each program to verify the compiled build's available command-line options. The compile command above is based on the current source tree; it has **not** been executed against every supported Linux environment as part of this guide.

### Alternative: verified official Linux release

For teams that prefer precompiled binaries, the official v0.2.1 Linux x86_64 archive is at:

https://github.com/feelcoin-org/feelcoin/releases/tag/v0.2.1

Verify the release artifact with the published checksum before execution. The SHA-256 displayed in the official v0.2.1 README for `feelcoin-v0.2.1-linux-x64.tar.gz` is:

```text
162b89f887e9df7572447c0d650fd8ed97f494cf97ccc17a9477ae214bf5adb1
```

Source compilation and the release archive are alternative installation approaches; **do not mix binaries from different commits** in one deployment.

## 4. Run a local full node

In the following examples, run commands from the folder containing the compiled binaries, or put those binaries on your secured `PATH`.

```bash
# Create a restricted directory for node data.
install -d -m 700 "$HOME/feelcoin-node-data"

# Keep administrative RPC on the loopback interface.
./feelcoind \
  --data-dir "$HOME/feelcoin-node-data" \
  --rpc-bind-ip 127.0.0.1 \
  --rpc-bind-port 35781
```

The v0.2.1 release has automatic bootstrap peers. If network discovery does not work, verify outbound TCP connectivity to the two official peers listed in Section 1. Peer connectivity uses TCP 35780. Do **not** open daemon RPC TCP 35781 to the public internet.

From the same host, check daemon status:

```bash
curl -fsS http://127.0.0.1:35781/get_info
```

Confirm that peer connectivity is healthy and the daemon has reached the network tip before enabling deposits. Recheck sync continuously; a healthy HTTP response **alone** does not prove the node is synchronized or on the expected mainnet chain.

For production, run the daemon under a dedicated unprivileged service account, with an audited service manager, controlled restart behavior, alerting, and node-data backups as appropriate. Do not use a public statistics API in place of node validation.

## 5. Create an operator-controlled wallet

Create a test wallet locally, not on a public web wallet or a shared workstation:

```bash
install -d -m 700 "$HOME/feelcoin-wallets"

./feelcoin-wallet-cli \
  --daemon-address 127.0.0.1:35781 \
  --generate-new-wallet "$HOME/feelcoin-wallets/integration"
```

Follow the interactive prompts. Store the recovery seed and private spend key **offline**, in a separate trusted custody process; never put them into tickets, Discord, email, repository files, screenshots, or application logs. Secure the encrypted wallet file and confirm that a recovery drill succeeds **before** any real deposits.

### Start wallet RPC (local network only)

The RPC service normally needs the encrypted wallet's password in a protected password file. An administrator can create one interactively without placing the password directly on a shell command line:

```bash
umask 077
read -r -s -p 'Wallet file password: ' WALLET_PASSWORD
printf '\n'
printf '%s' "$WALLET_PASSWORD" > \
  "$HOME/feelcoin-wallets/integration.password"
unset WALLET_PASSWORD
chmod 600 "$HOME/feelcoin-wallets/integration.password"
```

Then run the wallet RPC process:

```bash
./feelcoin-wallet-rpc \
  --wallet-file "$HOME/feelcoin-wallets/integration" \
  --password-file "$HOME/feelcoin-wallets/integration.password" \
  --daemon-address 127.0.0.1:35781 \
  --rpc-bind-ip 127.0.0.1 \
  --rpc-bind-port 35784
```

**Authentication is required.** Use the wallet RPC's supported authentication mechanism and store RPC credentials securely. Do not disable authentication for production, expose wallet RPC to the internet, or pass signing credentials through public proxies. Review `./feelcoin-wallet-rpc --help` for the exact release's credential options.

The password-file approach demonstrates functionality, not an ideal custody architecture: harden secret storage and process isolation before putting funds at risk.

## 6. Basic wallet JSON-RPC calls

From an authorized backend on the same host, POST JSON-RPC requests to:

`http://127.0.0.1:35784/json_rpc`

The examples use HTTP Digest credentials **as placeholders**. Replace `RPC_USERNAME:RPC_PASSWORD` with credentials provisioned by your wallet RPC service, preferably through an approved secret manager instead of a literal shell-history entry.

### 6.1 Read wallet balances

```bash
curl --digest --user 'RPC_USERNAME:RPC_PASSWORD' \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:35784/json_rpc \
  -d '{
    "jsonrpc":"2.0", "id":"1",
    "method":"get_balance",
    "params":{"account_index":0}
  }'
```

The response includes total and unlocked balances in **atomic units**. Do not treat the total balance as immediately spendable. Use integer arithmetic or arbitrary-precision types; JavaScript floating-point numbers are unsafe for many FEEL quantities.

### 6.2 Generate a unique deposit address

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "create_address",
  "params": {
    "account_index": 0,
    "count": 1,
    "label": "customer-reference-001"
  }
}
```

The wallet returns an address and its subaddress index. Record the mapping from **customer ID -> wallet account index -> subaddress index -> deposit address** in a durable database. For standard exchange deposit workflows, **use a distinct subaddress per customer** rather than having everyone share one deposit address.

### 6.3 Read incoming transfers

```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "get_transfers",
  "params": {
    "in": true,
    "pool": true,
    "pending": true,
    "out": false,
    "failed": false,
    "account_index": 0
  }
}
```

For each relevant incoming transfer, use its transaction ID, subaddress information, amount, block height, confirmation count, unlock status, and double-spend indicators. Deduplicate with an idempotent ledger key that includes the relevant output or subaddress identity; **transaction ID alone may not uniquely identify an individual customer's credit**.

### 6.4 Withdrawals: transfer request shape (illustrative only)

```json
{
  "jsonrpc": "2.0",
  "id": "4",
  "method": "transfer",
  "params": {
    "destinations": [
      {"amount": 1000000000000, "address": "VALID_DESTINATION_FEEL_ADDRESS"}
    ],
    "account_index": 0,
    "priority": 0,
    "get_tx_key": false
  }
}
```

This illustrates a **1 FEEL** withdrawal amount in atomic units. It is not ready to send until a valid destination, authenticated RPC client, wallet funds, a fee policy, and authorization controls are supplied. **Never automate customer withdrawals by submitting this example directly.** Build a withdrawal approval workflow with balance reservation, address validation, fee handling, rate limits, audit trails, and transaction reconciliation. Store transaction IDs and distinguish constructed, relayed, confirmed, failed, and replaced/retried states.

## 7. Deposit accounting policy

A recommended safe processing sequence is:

1. Register a unique customer deposit subaddress and persist its owner mapping.
2. Scan incoming wallet transfers regularly; store an immutable observation event.
3. Identify the correct customer and precise atomic-unit amount. Do not credit on an address or transaction-hash match alone.
4. Wait for your approved number of confirmations **and** any relevant output unlock requirements, then mark the deposit eligible for credit.
5. Perform a **single idempotent** ledger credit. Always reconcile credited balances against the wallet and blockchain.
6. Detect chain reorganizations, failed sync, double-spend indicators, and wallet restore/rescan events. Halt or reverse pending credits under an approved incident policy.

**Confirmation count:** Feelcoin targets 120-second blocks, but a target interval is not a security guarantee. This document does **not** prescribe a universal confirmation threshold; each operator must establish and periodically review it according to network conditions, deposit size, and risk appetite. Do not infer spendability solely from confirmations.

**Wallet refresh:** A fully synchronized daemon is necessary but is **not sufficient**; the wallet's scan height and observed transfers must also be current. After recovery or downtime, rescan and reconcile history before re-enabling credits.

## 8. Production controls and launch checklist

- **Isolation:** Restrict daemon RPC and wallet RPC to loopback or a tightly authenticated private network; never public internet endpoints.
- **Custody:** Separate hot-wallet limits, treasury/cold funds, backup authority, spending permissions, and recovery secrets.
- **Credentials:** Require wallet RPC authentication; rotate credentials; protect wallet/password files and secrets from logs and shell history.
- **Transaction safety:** Independently validate destination addresses; use atomic units; reserve balances; maintain idempotent withdrawal jobs and controls against duplicate broadcasts.
- **Sync and reliability:** Monitor daemon peer count, height, hash/tip consistency, wallet refresh, queue lag, unlock status, and chain reorganizations.
- **Accounting:** Reconcile wallet inputs/outputs, fees, pending amounts, subaddress ownership, and internal customer ledger records continuously.
- **Testing:** Exercise small-value deposits, many subaddresses, delayed confirmations, downtime, restored wallets, RPC failures, insufficient funds, and simulated reorganizations before launch.
- **Change management:** Pin versions and source commits; stage upgrades; compare release behavior; test wallet recovery; retain roll-back procedures without accidentally reversing finalized customer ledger entries.
- **Incident response:** Define when deposits or withdrawals are paused, how users are notified, and how an inconsistent ledger is repaired.

**Go-live gate:** Keep customer deposits and withdrawals disabled until the integration passes a full end-to-end test and a separate security/operational review.

## 9. Official technical resources

| Resource | URL |
|---|---|
| Feelcoin Core source | https://github.com/feelcoin-org/feelcoin |
| Core releases | https://github.com/feelcoin-org/feelcoin/releases |
| Release notes for v0.2.1 | https://github.com/feelcoin-org/feelcoin/releases/tag/v0.2.1 |
| Public API reference (read-only) | https://api.feelcoin.org/docs |
| Public API integration notes | https://github.com/feelcoin-org/feelcoin/blob/main/docs/PUBLIC_API.md |
| Block explorer | https://explorer.feelcoin.org |
| Official project | https://feelcoin.org |
| Technical contact | support@feelcoin.org |

*Feelcoin - In Feels We Trust.*

**Document status:** General-purpose technical tutorial. Command lines reflect the public Feelcoin source/release referenced above; users must validate their chosen environment and software revision independently. This document is not an audit, a security warranty, or a promise of compatibility with every trading system.