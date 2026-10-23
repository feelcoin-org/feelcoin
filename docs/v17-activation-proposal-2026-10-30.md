# Feelcoin v17 — provisional October 30, 2026 activation proposal

**STATUS: PROPOSAL ONLY — NOT SCHEDULED IN CONSENSUS CODE.**
No v17 activation entry has been inserted into `src/hardforks/hardforks.cpp`. No production release is authorized by this document.

## Reference chain snapshot

- Source: https://api.feelcoin.org/v1/network
- Observed 2026-10-23T09:54:33Z: chain height **15,489**, tip height **15,488**, target interval **120 seconds**.
- Candidate activation: **block 20,500**.
- From tip height 15,488, 5,012 block discoveries are needed through block 20,500 inclusive.
- At nominal target: 5,012 × 120 seconds = 601,440 seconds = **6 days, 23 hours, 4 minutes**.
- Reference projected time: **2026-10-30 ~08:58 UTC / 09:58 Algeria time**.
- **This date is not guaranteed.** The live network has experienced difficulty/interval volatility and can reach height 20,500 earlier or later.

## Desired communication timeline (conditional)

- October 23: aim to publish a **tested, signed, activation-height-configured final v17 upgrade** only if all consensus-critical checks, testnet validation, builds, and network coordination have passed. Announce the exact height, requirements, compatible miners/pools, and upgrade instructions. Otherwise communicate a progress update, not a mandatory release.
- Before the fork: independent pools and node operators validate upgrade, check node peers and chain tips, and explicitly acknowledge readiness. Complete testnet runs/reorg tests and ensure a viable network path.
- Before the **final** release: commit the confirmed activation height into mainnet consensus schedule, review the resulting binary and test its exact activation boundary, produce/verify release artifacts, and publish an unambiguous official upgrade notice. Never distribute software with an unreviewed activation.
- October 30: height 20,500 becomes effective **only if** the final, fully tested v17 release has been shipped with the exact scheduled activation and operators have had approximately seven days' notice. **If the final release is not ready on October 23, select and announce a later activation height rather than compressing the community's upgrade window.**

## Mandatory release gates

- All required CI build/test jobs green, including native Linux & Windows; compatible macOS where distributed.
- Historical v16 blockchain replay is byte-for-byte/consensus-identical through height H-1.
- LWMA v17 difficulty calculation and timestamp rules produce deterministic accepted/rejected results at H, H+1, and across alternate-chain reorganizations crossing H.
- No unexpected changes to RandomX, block target, 12 decimals, tail emission, 2% consensus-enforced treasury, addresses, balances, miner/pool reward calculation.
- Full-node testnet including mining pools, solo miners, wallet backends, and a previously v16-only node upgrading.
- Confirm signed release artifacts, reproducible checksums, documented upgrade/rollback-before-fork procedure, and upgraded nodes/pools reaching expected hashpower.
- No unresolved consensus-critical vulnerabilities. Independently review the change set.
- Upgrade-notice lead time is sufficient in practice. **If not, postpone activation.** Never force an untested change merely to meet the calendar.

## Miners and pools

- Pool miners using unchanged RandomX and a compatible Stratum implementation usually do not need to replace their miner binary, but this must be **validated** against upgraded pools.
- Pool operators and direct daemon/solo operators **must upgrade their consensus daemon** before activation. Pool compatibility has to be verified and any required pool update distributed.
- Node upgrades before block H must preserve v16 behavior until H. Non-upgraded nodes may follow an incompatible chain after H.

## Suggested public announcement draft (DO NOT POST UNTIL RELEASE IS VERIFIED)

> Feelcoin Core v0.3.0 — v17 upgrade preparation: proposed activation at block **20,500** (approximately October 30, 2026; actual time depends on mining). Node and pool operators will need to upgrade before activation. RandomX and wallet addresses remain unchanged, and 2% of the block subsidy continues to go to the treasury. We will publish verified binaries, checksums, instructions and the confirmed activation height after testing is complete. **Until the final release notice, this height is provisional.**
