# Feelcoin v17 — deployment checklist and community notice (DRAFT)

**Status: NOT APPROVED FOR PRODUCTION.** No v17 activation height or calendar date is configured. Keep Node1, Node2, pools and community miners on v16 until the full checklist is satisfied. This document is a release preparation draft, **not a release authorization**.

## Completed independent lab gates (October 23, 2026)

- Stage 1: isolated daemon build, C++ LWMA/timestamp unit tests, v16→v17 fakechain activation.
- Stage 2: offline reorg, independently checked v17 difficulty and mining.
- Stage 3: 29 successive dynamic-difficulty blocks across two chains and cumulative-work reorganization.
- Stage 4: 1,460 C++ LWMA and 141 timestamp cases matched an independent Python reference; multiple >90-step simulations.
- Stage 5: malformed/obsolete/future/past block rejection, alternative-chain validation, restart persistence.
- Stage 6: full sync to actual v16 mainnet chain height 15,651, with 30 sampled parent-linked header/work checks.
- Stage 7: isolated loopback P2P auto-propagation in both directions, partition and heavier-branch convergence.

All tests above passed in their stated scope. Fixed-difficulty fakechain tests and synthetic retarget sequences are **not substitutes for an independently audited real mainnet activation**.

## Gates to clear before v17 mainnet activation

1. **Mixed-version upgrade rehearsal**. Run `tests/v17/mixed_version_release_gate.py` on spare Contabo VPS, using a pinned original v16 binary and isolated v17 regtest. Confirm that old v16 nodes retain the legacy chain after height 120 and upgraded v17 peers converge, plus rejection of obsolete v16 blocks on new nodes. Stage 8 is **prepared, not yet passed**.
2. **Consensus/code review**. Independent engineer reviews timestamp handling (main and alternative chains), exact LWMA window arithmetic, signed/unsigned overflows, reorgs, treasury payouts, RandomX validation and miner incentives. Resolve critical/high issues before release.
3. **Economic invariants**. On a disposable testnet, verify coinbase outputs (miners/2% treasury), emission and tail reward, decimal scaling, spend/receive and wallet balance continuity before and after fork.
4. **Node / mining infrastructure**. Test upgraded full nodes, mining pools, daemon RPC, explorer and public API compatibility and recovery after service restart. Publish signed/checksummed release binaries. Windows is separately evaluated by the project owner on a real Windows machine before recommending the Windows build.
5. **Activation coordination**. After the foregoing gates pass, select a **future** block height with at least seven days' operator/community notice and margin for delays. Align Node1, Node2, pool operators, exchanges and public peers on the upgrade binaries *before* activation.
6. **Rollback and observability**. Snapshot the production DB and wallet backups, define who can intervene, verify hash/height/consensus status from independently hosted nodes, arrange rollback rehearsal **before** activation. **Never** blindly downgrade an active v17 chain to incompatible v16 after activation.
7. **Community notice**. Publish the exact height, approximate UTC time, verified binaries and checksums, miner/pool steps, and contacts only **after** the height is committed to an audited release and nodes are confirmed ready.

## Staged node deployment runbook (not commands)

- Verify final candidate source tree and signed/checksummed release artifacts; document the final version and deterministic build hash.
- Announce upcoming height after the documented notice period. Prior to activation, update the less-critical standby **Node2 first** with service backup and rollback tested; verify peers, RPC, same pre-fork block hash and synchronized chain.
- Observe Node2, then stage Node1 using a separate backup, preserving production RPC security and wallet files. Verify Node1/Node2 share the exact pre-fork tip with a third independent node.
- Monitor post-fork height, block versions, treasury coinbase, difficulty and block interval, block acceptance, peers and pools; publish a concise status bulletin.
- Never merge `test/v17-isolated-regtest` into main or deploy its fakechain schedule as a mainnet upgrade.

## Draft community announcement — DO NOT PUBLISH YET

**Feelcoin v17 — upcoming protocol upgrade**

We are preparing Feelcoin v17, a protocol update focused on difficulty adjustment and timestamp validation. The objective is more predictable operation when mining hashrate changes, while preserving RandomX CPU mining, the 120-second block target, the 2% transparent treasury, the existing monetary rules and wallet balances.

**No action is required right now.** The network continues to operate under v16. Once final testing, audits and operator coordination are complete, we'll announce a confirmed activation block height, approximate UTC time, download links, checksums and upgrade instructions with advance notice for nodes, pools and miners.

We do not ask the community to install test-only binaries or switch to a different chain.

In Feels We Trust. 🦊

## Draft final go/no-go record

- Linux test stages 1–7: PASS (scope-limited)
- Stage 8 original-v16/mixed-v17: PENDING EXECUTION
- Independent consensus review: NOT YET VERIFIED
- Economic/pool/RPC end-to-end check: NOT YET VERIFIED
- Release artifact integrity and signatures: NOT YET VERIFIED
- Windows evaluation: OWNER-LED, SEPARATE
- Activation height/date: **NOT SCHEDULED**
- Mainnet deployment permission: **NOT GRANTED**
