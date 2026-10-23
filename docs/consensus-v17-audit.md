# Feelcoin v17 consensus upgrade — audit and implementation gate

Status: **candidate implementation and unit tests committed on a draft PR; not activated**. No consensus activation has been scheduled. Do not merge or deploy without full builds, consensus replay, deterministic integration tests and independent review.

## Invariants

- Preserve 120-second target, RandomX, 12 decimal places, the current emission schedule, existing balances and transaction history.
- Preserve existing consensus-enforced **2% treasury** logic in `Blockchain::validate_miner_transaction`. Do not change allocations or addresses.
- Before activation height, return exactly the existing v16 difficulty on every path.
- Activation height remains **unset** until upgrade readiness and stakeholder coordination are verified.

## Verified source observations (main as inspected 2026-10-23)

- `src/cryptonote_config.h`: DIFFICULTY_WINDOW=720, LAG=15, CUT=60, TARGET_V2=120.
- `src/cryptonote_basic/difficulty.cpp`: `next_difficulty` sorts timestamps and trims tails; handles 128-bit cumulative difficulty. This is **not LWMA**.
- `src/cryptonote_core/blockchain.cpp`:
  - `get_difficulty_for_next_block`: normal-chain calculation with rolling cache.
  - `get_next_difficulty_for_alternative_chain`: alternate-chain calculation.
  - `recalculate_difficulties`: recalculation across historical heights.
  - Coinbase verification checks the Feelcoin treasury output.
- `src/hardforks/hardforks.cpp`: mainnet/testnet/stagenet currently list versions up to 16, from block 1.


## Candidate branch implementation (2026-10-23)

- `src/cryptonote_basic/feelcoin_lwma.h`: integer-only 90-block LWMA candidate, chronological timestamps, 6× target solvetime cap, monotonic virtual timestamps, minimum weighted-solvetime floor, 256-bit intermediates and 128-bit result checks.
- `src/cryptonote_core/blockchain.cpp`: same version-based dispatch (v16 legacy vs future v17 LWMA) used on main-chain mining, alternate-chain validation, and historical difficulty recalculation.
- `tests/unit_tests/difficulty.cpp`: candidate C++ tests for normal/fast/slow solvetimes, 60/90 windows, newest-history selection, invalid inputs and wide arithmetic.
- `tests/difficulty/feelcoin_lwma_simulation.py`: reproducible synthetic 100-seed comparison. Results are illustrative, **not network measurements**.

Illustrative synthetic average solve time in first 25 blocks after an abrupt network hashrate change:

| New / old hashrate | N=60 | N=90 |
|---|---:|---:|
| 0.1× | 653 s | 749 s |
| 0.5× | 200 s | 211 s |
| 2× | 76 s | 71 s |
| 10× | 20 s | 17 s |

N=60 generally reacts faster to hashrate crashes. N=90 is a more conservative candidate and **not final**. This experiment alone cannot establish resistance to timestamp manipulation, real network churn, or chain reorganizations.

**Emission accounting audit finding:** `get_block_reward` in `src/cryptonote_basic/cryptonote_basic_impl.cpp` currently subtracts the 64-bit `already_generated_coins` from the 64-bit `MONEY_SUPPLY` without a saturation check. The tail subsidy is separately enforced, but when generated coins exceed `MONEY_SUPPLY`, unsigned subtraction could wrap and distort rewards; ultimately 64-bit cumulative atomic supply also has a ceiling. This is a future consensus/economic correctness risk, not evidence of a current chain incident. A safe 128-bit accounting migration (including persistent DB/RPC formats) and exact old-chain replay require a separate reviewed change; leave existing emission and 2% treasury behavior unchanged until proven safe.\n\n**Critical open risks:** Current source has `CRYPTONOTE_BLOCK_FUTURE_TIME_LIMIT=7200` seconds and `BLOCKCHAIN_TIMESTAMP_CHECK_WINDOW=60`. Validate timestamp security together with LWMA; do not activate a v17 algorithm while these conditions are unreviewed. The chain-level v16 replay and full production build have not passed yet. The 2% treasury coinbase validation and emission code have not been modified.

## Implementation specification — still to be validated

1. Select and document an exact integer-arithmetic LWMA variant and window after simulations (candidate N=60–90). No floating-point operations in consensus.
2. Use chronological timestamps with bounded solvetime and cumulative work, with defined handling of duplicate/decreasing timestamps and startup history.
3. Guard overflow, division by zero, minimum difficulty, and any increase/decrease limits; keep fixed-difficulty test overrides intact.
4. Add a **version/height-aware** dispatch retaining the legacy algorithm for all historical heights and selecting LWMA only at the configured activation height.
5. Ensure main chain, alternate chain, recalc, and difficulty history/verification use matching inputs and activation rules. Any adjusted window selection must be identical across paths.
6. Test v16 replay equivalence, activation boundary, fork/reorg at activation, adversarial timestamps, rapid hashrate changes, stable hashrate, zero/maximum values and 128-bit boundaries. Build both Linux and Windows and synchronize a private test network.
7. Separately audit timestamp rules and supply accounting. These are **not approved changes** just by appearing in this plan; each needs its own deterministic safety case.
8. Only after successful reviews and testnet adoption, coordinate node/pool/wallet releases, set a sufficiently future activation height and announce it publicly.

## Explicitly out of scope

- Treasury changes, fee changes, premine, emission changes, historical chain reset.
- Mining pool deployment before consensus upgrade validation.
