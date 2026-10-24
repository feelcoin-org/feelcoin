# Feelcoin v17 — selected target block 21,205

**Developer decision on October 24, 2026: target block 21,205 for coordinated Core v1.0 + Desktop v1.0 launch and protocol v17 preparation.** This is a **provisional release-planning target, not yet encoded in mainnet consensus**. No activation is currently live.

## Calculation
- Developer-reported latest chain height: **16,144**.
- Observed average block interval used: approximately **119.5 seconds/block**, based on recent data; not a guarantee.
- One week = **604,800 seconds**, or **~5,061 blocks** at that pace.
- **16,144 + 5,061 = 21,205**.
- Height **18,400** and illustrative **23,000** are superseded; do not imply either was selected.

## Release and network-safety conditions
- Developer wants to **publish all matching v1.0 Core and Desktop Linux/Windows packages today, October 24**, and upgrade **Node1 and Node2 before the hardfork**.
- The exact version 17 activation height **must be included in the final reviewed mainnet release build**, and rehearsed at the actual height. Previous unsigned QA candidate still contains v16 mainnet schedule (no v17 activation) and is unsuitable for deployment.
- **Critical:** Seven days of projected blocks counted from this snapshot is NOT seven days' public notice after the approved packages are published. A faster network or delayed publication could cause height 21,205 to arrive too soon. Check live height and speed immediately before any actual activation scheduling; if seven full days' upgrade notice cannot be honored, obtain explicit agreement on a later height before changing production nodes.
- No merging or deploying test-only fakechain schedules. Preserve 120-second target, emission, RandomX, miner reward, balances, and 2% consensus treasury.

## Release blockers
1. Independent final consensus/security review; re-test mainnet v16→v17 boundary at approved height, pool/node compatibility and rollback plan.
2. Windows CLI smoke test failed with `0xC0000135` (missing runtime DLL); wallet RPC still to be tested. Rebuild with trusted Windows DLLs only and check all executables run on a clean Windows system. Antivirus scan was clean for **earlier** candidate but must be repeated for changed binaries.
3. Full matching Core and Desktop Linux/Windows builds, SHA256, provenance, backups and upgrade instructions. Desktop v1.0 Linux DEB and AppImage must bundle compatible reviewed Core binaries.

## Strict Windows package allowlist
- Windows native `feelcoind.exe`, `feelcoin-wallet-cli.exe`, `feelcoin-wallet-rpc.exe`, necessary verified **Windows** runtime `.dll` files, `README-CANDIDATE.txt`, `SHA256SUMS.txt`.
- NO Linux sources, header trees, `.so`, `.a`, `.deb`, `.AppImage`, scripts or build system directories. Verify file types/contents before publication.
- Do not disable security software, download random DLLs or release an incomplete wallet binary.

This is a planning document. It deliberately does not change production consensus or deploy nodes.
