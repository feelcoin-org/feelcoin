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

## Supply accounting — verified correction

The earlier concern about an inevitable unsigned-subtraction overflow was a **false positive**. Both the main-chain block acceptance path (`handle_block_to_main_chain`) and the alternative-chain metadata path in `src/cryptonote_core/blockchain.cpp` already saturate `already_generated_coins` at `MONEY_SUPPLY`. The `get_block_reward` subtraction is therefore safe for properly validated chains, including after tail emission starts. This saturation is intentional in the source comment and must be preserved.

**Remaining distinction:** the 64-bit `already_generated_coins` field is a capped *emission-curve input*, **not** a count of all coins ever minted after saturation. Tail block subsidies continue after the capped value reaches `MONEY_SUPPLY`; this is the intended unlimited tail-emission behavior. Don't replace the capped value with an uncapped 128-bit value inside `get_block_reward` or change the on-chain treasury distribution.

**Solution for accurate total-issued supply:** add a **separate 128-bit off-chain accounting/indexer** summing validated coinbase **base rewards**, excluding transaction fees, over all main-chain blocks. It must rollback orphaned blocks on reorgs and publish decimal strings in RPC/API to avoid JSON integer precision limits. Backfill and independently reconcile with sampled blocks. This does **not** require a consensus hard fork. A more invasive on-chain 128-bit storage migration should be considered only if a demonstrated consensus requirement demands it.

## Timestamp hardening — proposal requiring testing

Current main-chain `check_block_timestamp(const block&)` enforces a future bound relative to node wall-clock time of 7200 seconds plus a median of the last 60 timestamps. The alternative-chain `check_block_timestamp(vector&, const block&)` enforces the median but **does not directly enforce the same wall-clock future bound** at that entry point; assess subsequent reorg validation before drawing exploit conclusions.

Proposed v17-only changes for testing, **not committed or approved**:

1. Test reducing the permissible future offset from two hours to **30 minutes**, with a measured clock-skew margin and upgrade coordination; reject if legitimate miners/nodes are affected. Do not retroactively impose the new bound on historical v16 blocks.
2. Use a single height/version-aware future-time helper for main-chain and alternative-chain processing, with a carefully reviewed reorg/validation flow. Include checks for clock-boundary revalidation behavior.
3. Retain median-time-past checks and LWMA's per-solvetime clamp. These protect against different classes of timestamp manipulation, and neither substitutes for the other.
4. Test old/new version boundary, a chain reorganizing across the boundary, far-future timestamps, 30-minute boundaries, time drift, and adversarial consecutive timestamps.

**Open gates:** Full production builds, historical v16 replay, timestamp/adversarial testnet simulations, and consensus peer review have not passed. Treasury validation and emission amounts remain unchanged.

## Implementation specification — still to be validated

1. Select and document an exact integer-arithmetic LWMA variant and window after simulations (candidate N=60–90). No floating-point operations in consensus.
2. Use chronological timestamps with bounded solvetime and cumulative work, with defined handling of duplicate/decreasing timestamps and startup history.
3. Guard overflow, division by zero, minimum difficulty, and any increase/decrease limits; keep fixed-difficulty test overrides intact.
4. Add a **version/height-aware** dispatch retaining the legacy algorithm for all historical heights and selecting LWMA only at the configured activation height.
5. Ensure main chain, alternate chain, recalc, and difficulty history/verification use matching inputs and activation rules. Any adjusted window selection must be identical across paths.
6. Test v16 replay equivalence, activation boundary, fork/reorg at activation, adversarial timestamps, rapid hashrate changes, stable hashrate, zero/maximum values and 128-bit boundaries. Build both Linux and Windows and synchronize a private test network.
7. Audit timestamp rules with main/alternative-chain parity; accurate uncapped supply reporting can be implemented off-chain, separate from consensus. Neither constitutes an approved consensus change.
8. Only after successful reviews and testnet adoption, coordinate node/pool/wallet releases, set a sufficiently future activation height and announce it publicly.

## Explicitly out of scope

- Treasury changes, fee changes, premine, emission changes, historical chain reset.
- Mining pool deployment before consensus upgrade validation.
