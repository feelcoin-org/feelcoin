// Copyright (c) 2026 Feelcoin contributors.
// Candidate consensus timestamp policy for v17. Not active on mainnet.
#pragma once

#include <cstdint>
#include <limits>

namespace cryptonote
{
  // Legacy future-time tolerance is preserved for pre-v17 blocks.
  static constexpr std::uint64_t FEELCOIN_LEGACY_FUTURE_SECONDS = 2 * 60 * 60;
  static constexpr std::uint64_t FEELCOIN_V17_FUTURE_SECONDS = 30 * 60;

  inline std::uint64_t feelcoin_future_timestamp_allowance(std::uint8_t version)
  {
    return version >= 17 ? FEELCOIN_V17_FUTURE_SECONDS
                         : FEELCOIN_LEGACY_FUTURE_SECONDS;
  }

  // Overflow-safe inclusive future-time comparison.
  // Call only with a consensus-validated version, as the consensus schedule
  // (not the untrusted version claimed by a block) determines the rules.
  inline bool feelcoin_timestamp_within_future_limit(
    std::uint64_t block_time, std::uint64_t now, std::uint8_t version)
  {
    const std::uint64_t allowance = feelcoin_future_timestamp_allowance(version);
    const std::uint64_t max_time = std::numeric_limits<std::uint64_t>::max();
    const std::uint64_t upper_bound =
      now > max_time - allowance ? max_time : now + allowance;
    return block_time <= upper_bound;
  }
}
