#include <iostream>
#include <string>

#include "cryptonote_basic/cryptonote_basic_impl.h"
#include "cryptonote_basic/cryptonote_format_utils.h"
#include "cryptonote_core/cryptonote_tx_utils.h"
#include "string_tools.h"

int main(int argc, char** argv)
{
    if (argc != 2)
    {
        std::cerr << "Usage: feelcoin-genesis <Feelcoin address>\n";
        return 1;
    }

    cryptonote::address_parse_info info{};

    if (!cryptonote::get_account_address_from_str(
            info,
            cryptonote::MAINNET,
            argv[1]))
    {
        std::cerr << "Invalid Feelcoin mainnet address\n";
        return 1;
    }

    if (info.is_subaddress || info.has_payment_id)
    {
        std::cerr << "Use a primary Feelcoin address\n";
        return 1;
    }

    cryptonote::transaction tx;

    const cryptonote::blobdata extra_nonce =
        "Feelcoin Genesis | In Feels We Trust | 2026-10-01";

    if (!cryptonote::construct_miner_tx(
            0,
            0,
            0,
            0,
            0,
            info.address,
            tx,
            extra_nonce,
            1,
            1))
    {
        std::cerr << "Failed to construct Feelcoin genesis transaction\n";
        return 1;
    }

    const cryptonote::blobdata blob = cryptonote::tx_to_blob(tx);

    std::cout << "GENESIS_TX="
              << epee::string_tools::buff_to_hex_nodelimer(blob)
              << "\n";

    std::cout << "GENESIS_REWARD_ATOMIC="
              << cryptonote::get_outs_money_amount(tx)
              << "\n";

    return 0;
}
