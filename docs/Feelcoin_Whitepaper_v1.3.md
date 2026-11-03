# Feelcoin Technical Whitepaper — Protocol v17 Update (v1.3)

**FEEL · Independent RandomX Proof-of-Work network**  
**Updated:** 1 November 2026  
**Status:** Technical update to the published [Feelcoin Whitepaper v1.2](./Feelcoin_Whitepaper_v1.2.pdf)

> This version documents the deployed v17 protocol. It supplements v1.2 and supersedes statements in earlier versions that describe the v17 upgrade as pending. The consensus implementation and chain history, not this document, define the network's authoritative behavior. This is a technical document, not investment advice.

## 1. Purpose and design

Feelcoin is an independently launched, Monero-derived proof-of-work blockchain using RandomX to enable general-purpose CPU mining. Its design emphasizes verifiable monetary rules, public-source implementations, non-custodial ownership, and independent network participation. Mainnet launched in October 2026.

## 2. Network and identifiers

| Parameter | Mainnet value |
| --- | --- |
| Ticker | FEEL |
| Consensus | RandomX Proof of Work |
| Target block interval | 120 seconds |
| Monetary precision | 12 decimal places |
| Mainnet P2P port | 35780 |
| Mainnet daemon RPC port | 35781 |
| Mainnet ZMQ RPC port | 35782 |
| Protocol upgrade | v17, activated at height 21,205 |

The block interval is a *target*, not a guarantee. Real block intervals vary with mining participation, difficulty and probabilistic block discovery.

## 3. v17 consensus upgrade: LWMA

**Activation:** mainnet block **21,205**. Network operators must run a compatible v17 daemon after activation to remain on the intended main chain.

The upgrade introduces an integer-only, **90-block Linearly Weighted Moving Average (LWMA)** difficulty adjustment. LWMA weights recent solve times more heavily when updating difficulty, helping the network respond to changes in aggregate mining hashrate. The implementation uses 128-bit difficulty with wider intermediate arithmetic for numerical safety.

This adjustment does not guarantee a block every 120 seconds and cannot immediately produce blocks when the network has too little mining power. Difficulty changes take effect through new blocks.

The upgrade also tightens future-block timestamp acceptance to a 30-minute bound and aligns main-chain and alternative-chain difficulty validation. Details and edge cases are defined in the versioned Core source.

## 4. What v17 does *not* change

- The RandomX mining algorithm and 120-second block target.
- Existing wallet addresses, balances and 12-decimal precision.
- The established emission and tail-emission rules.
- The existing consensus-enforced 2% development treasury.
- The allocation of transaction fees to miners.

**No new developer fee** was introduced in the v17 hard fork. The optional use of a particular mining pool is distinct from protocol-level rules.

## 5. Block rewards, treasury and pool fees

Beginning at block **590**, consensus requires a development-treasury output equal to **2% of the block subsidy**. The remaining **98% of the subsidy** belongs to the mining side, before any optional pool-service fees. Transaction fees are not split into the treasury: **100% of transaction fees remain with miners**.

The treasury is a division of the existing subsidy, **not additional monetary issuance**. Its consensus rules can be verified in `src/cryptonote_core/feelcoin_treasury.h`, `src/cryptonote_core/cryptonote_tx_utils.cpp`, and block validation code.

The official Feelcoin pool charges a separate **0.5% pool-service fee**. Solo miners do not pay this pool-service fee. Other independent pools set their own policies; their terms should not be confused with consensus rules.

## 6. Mining, block production and difficulty risk

Mining shares submitted to a pool are not themselves confirmed mainnet blocks. Pool-reported hashrate is not a complete census of solo miners or other pools. When network hashrate drops quickly, blocks can be delayed until enough proof of work is found; LWMA can then lower difficulty as new blocks arrive.

Individual miners should use current software and confirm pool or solo mining connectivity, address validity, accepted shares and daemon synchronization. Hashrate and estimated returns are variable, and no profitability is guaranteed.

## 7. Wallets and operational security

Feelcoin offers CLI and RPC wallets and desktop and Android wallet distributions. Wallets remain non-custodial when keys are held by their owners. Protect mnemonic seeds and private spend keys; keep offline backups. Verify official release checksums. Do not expose daemon or wallet RPC interfaces openly to the internet.

Network upgrades may require an updated local daemon, while ordinary users connecting to a compatible pool do not necessarily have to update their mining client.

## 8. Pool accounting and payout integrity

The official pool uses durable payout intent locking to guard against duplicate transfers when the wallet RPC response is missing or uncertain. After a transfer is independently verified, corresponding miner balances and payment records can be reconciled atomically. An interrupted RPC response must **never** trigger blind rebroadcast of the same payment.

As of this document's date, production has a longer wallet-RPC timeout and verified successful automatic settlements after the change. Fully automated transaction-aware recovery from ambiguous transfers remains a planned improvement. This operational mechanism is **not a consensus rule**.

## 9. Open source, verification and decentralization

Feelcoin's public source repositories, node and explorer tools make independent inspection possible. The codebase acknowledges its Monero-derived lineage. Neither the website, pool nor explorer independently defines consensus; validating full nodes do.

Independent pools and nodes improve resilience and limit reliance on one operator. Third-party services, market listings, and exchanges are not guaranteed, and independent third-party services are not officially endorsed merely because they list FEEL.

## 10. Status, limitations and roadmap

The October 2026 launch was followed by the Core v1.0.0/v17 upgrade, desktop and Android wallet development, public infrastructure, and independent mining-pool participation. Near-term engineering priorities include payout-recovery automation, independent node documentation, third-party pool interoperability, reproducible builds, wallet security guidance, service monitoring and public developer APIs.

See [Public Roadmap](./ROADMAP.md) for the current direction. A roadmap is a statement of intentions, **not a promise of delivery dates, token value, price performance, or exchange listings**.

## 11. Primary technical references

- [Feelcoin Core source](https://github.com/feelcoin-org/feelcoin)
- [Core v1.0.0 release notes](https://github.com/feelcoin-org/feelcoin/releases/tag/v1.0.0)
- [Protocol configuration](https://github.com/feelcoin-org/feelcoin/blob/main/src/cryptonote_config.h)
- [Difficulty source](https://github.com/feelcoin-org/feelcoin/blob/main/src/cryptonote_basic/difficulty.cpp)
- [Consensus treasury header](https://github.com/feelcoin-org/feelcoin/blob/main/src/cryptonote_core/feelcoin_treasury.h)
- [Pool source](https://github.com/feelcoin-org/feelcoin-pool)
- [Public Roadmap](./ROADMAP.md)

---

**Version history:** v1.2 — original published technical paper; v1.3 (1 November 2026) — current protocol/operations update reflecting mainnet v17 activation. No protocol or monetary change is introduced by publishing this document.

*In Feels We Trust.*
