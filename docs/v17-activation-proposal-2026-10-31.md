# Feelcoin v17 — seven-day minimum mainnet upgrade notice (October 24, 2026 proposal)

**STATUS: NO HEIGHT OR DATE SELECTED. The developer has explicitly rejected treating 23,000 as a chosen target. NO MAINNET ACTIVATION IS CODED, ANNOUNCED, OR AUTHORIZED HERE.** The old October 30 / height 18,400 estimate is superseded.

## Verified inputs (UTC)

- Snapshot at **2026-10-24 07:30:26 UTC**: chain height **16,126** (tip index **16,125**), network difficulty **8,389,469**, estimated network hashrate **69,912.242 H/s**, protocol target **120 seconds**. [Official network API](https://api.feelcoin.org/v1/network).
- Supply snapshot at **07:30:53 UTC**: **463,888.296253615093 FEEL** emitted, source height **16,127**; this is *protocol-issued* supply, not independently verified circulating supply, excludes transaction fees. [Official supply API](https://api.feelcoin.org/v1/supply).
- [Official recent blocks API](https://api.feelcoin.org/v1/blocks/latest): block **16,126**, timestamp **1792826949** (07:29:09 UTC), subsidy/reward about **28.325486811128 FEEL**. Zero transactions in that block.
- [Veinpool block history](https://veinpool.fr/en/blocks) lists FEEL block **15,569** at **2026-10-23 13:00 UTC** (minute resolution). Difference 557 block indices over approximately 18 hours 29 minutes => **~119.5 sec per block** across that period. This is cross-source, approximate, short-history evidence, not a forecast guarantee.
- The treasury rule stays **2% of subsidy from block 590**, and miners get 98%. No change to emission, block target or monetary rules is proposed.

## Seven-day estimate and conservative height

- Requested minimum lead time: **7 full days from the public availability of approved binaries and operator announcement**. Earliest hypothetical start today at **2026-10-24 ~08:49 Africa/Algiers** gives earliest calendar date **2026-10-31 ~08:49 Africa/Algiers**, *but this is not yet a confirmed activation date*.
- At 120s/block the expected seven-day growth is **5,040 blocks**; from observed tip ~16,126, an exact-pace height is **~21,166**. Therefore a **21,200** fork is too close to guarantee that operators truly have seven days after release; a faster network would reach it early.
- **Illustrative scenario only: block height 23,000 is NOT agreed or selected**, and MUST NOT be called the activation target. Actual height remains **TBD** pending explicit project approval and release readiness. At snapshot height 16,126 it leaves **6,874 blocks**.
- Estimated arrival of height 23,000 from 2026-10-24 08:49 Africa/Algiers:
  - At 120s/block: **2026-11-02 around 21:57 Algeria time**, about 9.55 days.
  - At 90s/block: **2026-10-31 around 12:40 Algeria time**, about 7.16 days.
  - At 80s/block: **2026-10-30 around 17:35 Algeria time**, **under 7 days**. Therefore even this candidate is not a calendar-time guarantee.
- The earlier proposed block **18,400** is no longer acceptable: at 120s/block it is only about 3.2 days away from the snapshot.

## Strict activation safeguards

1. **Release gate**: finish independent consensus review, complete relevant Linux and Windows runtime/release-package checks, and verify testnet/mixed-version acceptance plus Node1, Node2 and pool readiness. Existing 8 VPS stages and unsigned Windows x64 candidate build passed, but that alone is not production release approval.
2. **Only after the final binaries are available for operators**, publish a public notice and freeze a height demonstrably at least seven days ahead under a conservative block-rate forecast (and revisit the estimate using recent 24–72h history). Delay the height if binaries, independent review or community upgrade readiness are late.
3. Do **not** claim the timestamp in a hardfork schedule guarantees wall-clock activation; the protocol forks based on validated chain height, and miners can change the rate. If a firm calendar minimum is mandatory, additional tested consensus rules or a larger safety buffer are required.
4. Do **not** merge the isolated `test/v17-isolated-regtest` fork-height 120 schedule into mainnet. The `mainnet_hard_forks` array remains v16; a future approved PR must explicitly add v17 with its final height and reproduce the mixed-version replay at that exact height.
5. Coordinate all v17-compatible Core and Desktop Wallet v1.0 packages and Node1/Node2/community pool operators before activation. Publish SHA256SUMS, release notes, upgrade instructions, rollback/backups and pre-activation monitoring.

**This file is planning documentation. It deliberately changes no consensus rules, production nodes, or user balances.**
