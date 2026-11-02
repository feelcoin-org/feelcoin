// Feelcoin v17 LWMA difficulty candidate. Not activated on mainnet.
// Based on the LWMA-1 family of integer-only retarget algorithms.
// See https://github.com/zawy12/difficulty-algorithms/issues/3
#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>
#include <boost/multiprecision/cpp_int.hpp>

namespace cryptonote
{
  // 90 blocks at a 120-second target: approximately a 3-hour observation window.
  static constexpr std::size_t FEELCOIN_LWMA_WINDOW = 90;

  // Input vectors are ordered oldest to newest and contain cumulative work,
  // not individual per-block difficulties. Last window + 1 points are used.
  // Return 0 for invalid input/overflow so consensus validation can reject it.
  inline boost::multiprecision::uint128_t next_difficulty_lwma(
    const std::vector<std::uint64_t>& timestamps,
    const std::vector<boost::multiprecision::uint128_t>& cumulative_difficulties,
    std::size_t target_seconds,
    std::size_t window = FEELCOIN_LWMA_WINDOW)
  {
    typedef boost::multiprecision::uint128_t difficulty_type;
    typedef boost::multiprecision::uint256_t wide_type;

    if (timestamps.size() != cumulative_difficulties.size() ||
        window == 0 || window > 120 || target_seconds == 0 ||
        timestamps.size() <= window ||
        target_seconds > std::numeric_limits<std::uint64_t>::max() / (6 * window * window))
      return 0;

    const std::size_t first = timestamps.size() - window - 1;
    const std::size_t last = timestamps.size() - 1;
    if (cumulative_difficulties[last] <= cumulative_difficulties[first])
      return 0;

    const std::uint64_t max_solvetime = 6 * static_cast<std::uint64_t>(target_seconds);
    std::uint64_t previous_timestamp = timestamps[first];
    std::uint64_t weighted_solvetimes = 0;
    for (std::size_t i = 1; i <= window; ++i)
    {
      const std::uint64_t timestamp = timestamps[first + i];
      std::uint64_t solvetime;
      if (timestamp > previous_timestamp)
      {
        solvetime = std::min(timestamp - previous_timestamp, max_solvetime);
        previous_timestamp = timestamp;
      }
      else
      {
        // Make out-of-order timestamps strictly increasing in the virtual
        // series, avoiding uint64 overflow at its maximum value.
        solvetime = 1;
        if (previous_timestamp != std::numeric_limits<std::uint64_t>::max())
          ++previous_timestamp;
      }
      weighted_solvetimes += static_cast<std::uint64_t>(i) * solvetime;
    }

    // Prevent a burst of near-zero solve times from causing unbounded difficulty.
    const std::uint64_t floor = std::max<std::uint64_t>(
      1, static_cast<std::uint64_t>(window * window * target_seconds / 20));
    weighted_solvetimes = std::max(weighted_solvetimes, floor);

    const wide_type work = wide_type(cumulative_difficulties[last]) -
                           wide_type(cumulative_difficulties[first]);
    // average(work) * target / weighted-average(solvetime), exactly in
    // integer arithmetic: (work/N)*T / (2*L/(N*(N+1))).
    const wide_type result = work * (window + 1) * target_seconds /
                             (2 * weighted_solvetimes);
    if (result > std::numeric_limits<difficulty_type>::max())
      return 0;
    return result == 0 ? difficulty_type(1) : result.convert_to<difficulty_type>();
  }
}
