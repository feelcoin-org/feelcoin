# Feelcoin v17 — provisional October 30, 2026 activation (revised)

**STATUS: PROPOSAL ONLY — NOT SCHEDULED IN CONSENSUS CODE; NOT RELEASED.**

## Observed live chain speed, not the 120-second target

- Public API: [network](https://api.feelcoin.org/v1/network) and [latest block timestamps](https://api.feelcoin.org/v1/blocks/latest).
- Snapshot as of **2026-10-23 10:49 UTC**: tip height **15,508**.
- Latest 10 consecutive headers: block **15,499 at 1792750262** and block **15,508 at 1792752144**.
- Average of 9 actual intervals: **1,882 / 9 = 209.11 seconds/block**.
- A seven-day projection at this *observed* pace: **604,800 / 209.11 ≈ 2,892 blocks**, giving **candidate fork height 18,400**.
- Approximate activation: **October 30 around 10:41 UTC (11:41 Algeria)** if the mean stays unchanged.
- Former proposed height 20,500 would take approximately **12.1 days** at this pace; **superseded**.

**High uncertainty**: Nine block intervals are too few for a reliable 7-day forecast in probabilistic mining. A stable 24–72-hour rolling sample with reorg handling should be used before freezing the height. If hashrate recovers toward the 120-second target, block 18,400 could arrive after only ~4 days. A height lock cannot guarantee a full seven-day warning. If adequate upgrade notice is required, select a later activation height and announce it only with tested release binaries.

## Windows-only Core candidate for antivirus evaluation

- Dedicated CI recipe: [v17-windows-candidate.yml](../.github/workflows/v17-windows-candidate.yml) runs on Windows with MSYS2, builds native x64, stages **only** `feelcoind.exe`, `feelcoin-wallet-cli.exe`, and `feelcoin-wallet-rpc.exe` plus README/SHA256.
- Excludes Linux executables, Linux source trees, .so, .AppImage, .deb and shell scripts from the final candidate ZIP by explicit allowlist and archive inspection.
- **Unsigned, unreleased QA artifact only**. GitHub Actions must successfully complete the build before any ZIP is available; verify hashes, test Windows Defender/SmartScreen while protection is enabled, and avoid running against valuable production wallet keys.
- Removing Linux files from a distribution ZIP alone does **not** guarantee that antivirus warnings disappear; code signing, reproducibility and vendor false-positive review may still be necessary.

## Release gates before scheduling activation

- Finish the consensus changes and testnet validation (LWMA, timestamp policy, branch/reorg handling, treasury invariants and emission).
- CI Linux, Windows, and unit tests green; validate the exact packaged executable from the final release branch.
- Coordinate upgraded nodes/pools, mining compatibility, and one-week community notice.
- Only then commit an agreed future activation height to the mainnet hardfork schedule, test that exact height, and publish signed/checksummed release binaries.
- If release or reviews are delayed, **recalculate a later fork height** and preserve the intended notice window. Do not set height 18,400 in code merely because this document mentions it.

This plan never modifies current mainnet consensus by itself.
