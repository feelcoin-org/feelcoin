#pragma once

#include <cstdint>

namespace cryptonote
{
namespace feelcoin_treasury
{

static constexpr uint64_t ACTIVATION_HEIGHT = 590;
static constexpr uint64_t PERCENT = 2;

static constexpr const char *ADDRESS =
  "FBXZD77V6Rac7o7Ukc16j8g6iPpu6LuV5Udi3UMgopATBGrbycUSTmXUQcm1B2bx8HMYyjZHxoEtqUokaUweUvWKMEbnBkc";

/*
 * Publicly disclosed treasury VIEW key.
 *
 * This is intentionally the PRIVATE VIEW KEY, not the spend key.
 * Publishing it allows every Feelcoin node to verify treasury
 * coinbase outputs while providing no ability to spend treasury funds.
 */
static constexpr const char *VIEW_SECRET_KEY =
  "ef7f80c3f3fdf074b3e9bf6c7276832f7935d54ff1c7e7f4e3b6e9352f3a940c";

inline uint64_t reward(uint64_t base_reward)
{
  return base_reward * PERCENT / 100;
}

inline bool active(uint64_t height)
{
  return height >= ACTIVATION_HEIGHT;
}

}
}
