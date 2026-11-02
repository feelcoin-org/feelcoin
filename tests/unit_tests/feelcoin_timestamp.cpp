// Feelcoin v17 timestamp policy tests. Hard fork activation is NOT scheduled.
#include <cstdint>
#include <limits>
#include "gtest/gtest.h"
#include "cryptonote_basic/feelcoin_timestamp_rules.h"

TEST(feelcoin_timestamp, preserves_legacy_two_hour_tolerance)
{
  constexpr std::uint64_t now = 1800000000ULL;
  ASSERT_EQ(7200, cryptonote::feelcoin_future_timestamp_allowance(16));
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(now + 7200, now, 16));
  ASSERT_FALSE(cryptonote::feelcoin_timestamp_within_future_limit(now + 7201, now, 16));
}

TEST(feelcoin_timestamp, v17_half_hour_boundary)
{
  constexpr std::uint64_t now = 1800000000ULL;
  ASSERT_EQ(1800, cryptonote::feelcoin_future_timestamp_allowance(17));
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(now + 1800, now, 17));
  ASSERT_FALSE(cryptonote::feelcoin_timestamp_within_future_limit(now + 1801, now, 17));
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(now - 1, now, 17));
  ASSERT_EQ(1800, cryptonote::feelcoin_future_timestamp_allowance(18));
}

TEST(feelcoin_timestamp, v17_safe_uint64_overflow_boundary)
{
  constexpr std::uint64_t max_time = std::numeric_limits<std::uint64_t>::max();
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(max_time, max_time - 200, 17));
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(max_time - 1, max_time, 17));
  ASSERT_FALSE(cryptonote::feelcoin_timestamp_within_future_limit(1801, 0, 17));
  ASSERT_TRUE(cryptonote::feelcoin_timestamp_within_future_limit(1800, 0, 17));
}
