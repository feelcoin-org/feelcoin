# Feelcoin v17 consensus upgrade — audit and implementation gate

Status: **design/audit only**. No consensus activation has been scheduled. Do not merge or deploy without deterministic tests and independent review.

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
