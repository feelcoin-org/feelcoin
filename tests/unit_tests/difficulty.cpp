// Copyright (c) 2019-2022, The Monero Project
// 
// All rights reserved.
// 
// Redistribution and use in source and binary forms, with or without modification, are
// permitted provided that the following conditions are met:
// 
// 1. Redistributions of source code must retain the above copyright notice, this list of
//    conditions and the following disclaimer.
// 
// 2. Redistributions in binary form must reproduce the above copyright notice, this list
//    of conditions and the following disclaimer in the documentation and/or other
//    materials provided with the distribution.
// 
// 3. Neither the name of the copyright holder nor the names of its contributors may be
//    used to endorse or promote products derived from this software without specific
//    prior written permission.
// 
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
// THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
// PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
// STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
// THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#include "gtest/gtest.h"
#include "int-util.h"
#include "cryptonote_basic/difficulty.h"
#include "cryptonote_basic/feelcoin_lwma.h"

static cryptonote::difficulty_type MKDIFF(uint64_t high, uint64_t low)
{
  cryptonote::difficulty_type d = high;
  d = (d << 64) | low;
  return d;
}

static crypto::hash MKHASH(uint64_t high, uint64_t low)
{
  cryptonote::difficulty_type hash_target = high;
  hash_target = (hash_target << 64) | low;
  boost::multiprecision::uint256_t hash_value = std::numeric_limits<boost::multiprecision::uint256_t>::max() / hash_target;
  crypto::hash h;
  uint64_t val;
  val = (hash_value & 0xffffffffffffffff).convert_to<uint64_t>();
  ((uint64_t*)&h)[0] = SWAP64LE(val);
  hash_value >>= 64;
  val = (hash_value & 0xffffffffffffffff).convert_to<uint64_t>();
  ((uint64_t*)&h)[1] = SWAP64LE(val);
  hash_value >>= 64;
  val = (hash_value & 0xffffffffffffffff).convert_to<uint64_t>();
  ((uint64_t*)&h)[2] = SWAP64LE(val);
  hash_value >>= 64;
  val = (hash_value & 0xffffffffffffffff).convert_to<uint64_t>();
  ((uint64_t*)&h)[3] = SWAP64LE(val);
  return h;
}

TEST(difficulty, check_hash)
{
  ASSERT_TRUE(cryptonote::check_hash(MKHASH(0, 1), MKDIFF(0, 1)));
  ASSERT_FALSE(cryptonote::check_hash(MKHASH(0, 1), MKDIFF(0, 2)));

  ASSERT_TRUE(cryptonote::check_hash(MKHASH(0, 0xffffffffffffffff), MKDIFF(0, 0xffffffffffffffff)));
  ASSERT_FALSE(cryptonote::check_hash(MKHASH(0, 0xffffffffffffffff), MKDIFF(1, 0)));

  ASSERT_TRUE(cryptonote::check_hash(MKHASH(1, 1), MKDIFF(1, 1)));
  ASSERT_FALSE(cryptonote::check_hash(MKHASH(1, 1), MKDIFF(1, 2)));

  ASSERT_TRUE(cryptonote::check_hash(MKHASH(0xffffffffffffffff, 1), MKDIFF(0xffffffffffffffff, 1)));
  ASSERT_FALSE(cryptonote::check_hash(MKHASH(0xffffffffffffffff, 1), MKDIFF(0xffffffffffffffff, 2)));
}


// Candidate v17 tests. The fork has no scheduled activation yet.
static cryptonote::difficulty_type TEST_LWMA_CONSTANT(
  uint64_t solvetime, uint64_t block_work, size_t window)
{
  std::vector<uint64_t> timestamps;
  std::vector<cryptonote::difficulty_type> cumulative;
  for (size_t i = 0; i <= window; ++i)
  {
    timestamps.push_back(1000000 + i * solvetime);
    cumulative.push_back(cryptonote::difficulty_type(i + 1) * block_work);
  }
  return cryptonote::next_difficulty_lwma(timestamps, cumulative, 120, window);
}

TEST(difficulty, feelcoin_lwma_steady_60_and_90)
{
  ASSERT_EQ(1000, TEST_LWMA_CONSTANT(120, 1000, 60));
  ASSERT_EQ(1000, TEST_LWMA_CONSTANT(120, 1000, 90));
}

TEST(difficulty, feelcoin_lwma_fast_and_slow_blocks)
{
  ASSERT_EQ(2000, TEST_LWMA_CONSTANT(60, 1000, 90));
  ASSERT_EQ(500, TEST_LWMA_CONSTANT(240, 1000, 90));
  ASSERT_EQ(166, TEST_LWMA_CONSTANT(720, 1000, 90));
}

TEST(difficulty, feelcoin_lwma_uses_newest_history)
{
  std::vector<uint64_t> timestamps;
  std::vector<cryptonote::difficulty_type> cumulative;
  for (size_t i = 0; i <= 110; ++i)
  {
    timestamps.push_back(1000000 + (i <= 20 ? i * 120 : 2400 + (i - 20) * 60));
    cumulative.push_back(cryptonote::difficulty_type(i + 1) * 1000);
  }
  ASSERT_EQ(2000, cryptonote::next_difficulty_lwma(timestamps, cumulative, 120));
}

TEST(difficulty, feelcoin_lwma_timestamp_and_input_guards)
{
  std::vector<uint64_t> timestamps(91, 1000000);
  std::vector<cryptonote::difficulty_type> cumulative;
  for (size_t i = 0; i <= 90; ++i)
    cumulative.push_back(cryptonote::difficulty_type(i + 1) * 1000);
  ASSERT_GT(cryptonote::next_difficulty_lwma(timestamps, cumulative, 120), 0);
  timestamps.assign(91, std::numeric_limits<uint64_t>::max());
  ASSERT_GT(cryptonote::next_difficulty_lwma(timestamps, cumulative, 120), 0);
  ASSERT_EQ(0, cryptonote::next_difficulty_lwma(timestamps, cumulative, 0));
  ASSERT_EQ(0, cryptonote::next_difficulty_lwma(timestamps, cumulative, 120, 121));
  ASSERT_EQ(0, cryptonote::next_difficulty_lwma(timestamps, {}, 120));
  cumulative.back() = 0; // Bad cumulative work must be rejected.
  ASSERT_EQ(0, cryptonote::next_difficulty_lwma(timestamps, cumulative, 120));
}

TEST(difficulty, feelcoin_lwma_128bit_work)
{
  const cryptonote::difficulty_type per_block = MKDIFF(1ULL << 55, 0);
  std::vector<uint64_t> timestamps;
  std::vector<cryptonote::difficulty_type> cumulative;
  for (size_t i = 0; i <= 90; ++i)
  {
    timestamps.push_back(1000000 + i * 120);
    cumulative.push_back(cryptonote::difficulty_type(i + 1) * per_block);
  }
  ASSERT_EQ(per_block, cryptonote::next_difficulty_lwma(timestamps, cumulative, 120));
}
