#!/usr/bin/env python3
"""Stage three: dynamic v17 LWMA retarget + alternative-chain reorg.

Runs on the dedicated Contabo VPS only. Uses existing synthetic smoke-test
blockchain, not mainnet; starts two offline fakechain daemons without
--fixed-difficulty. Per block, cross-checks the daemon's difficulty against
an independent calculation, then submits the longer dynamic-difficulty
branch to the competing node. No existing wallet or production DB touched.
"""
import pathlib
import re
import sys
import tempfile
import traceback
import next_stage_vps as lab

SOURCE = pathlib.Path(__file__).resolve().parents[2]


def check_mine(port, count, address, nonce_base, title):
    observed = []
    for index in range(count):
        height, _ = lab.current_tip(port)
        next_height = height + 1
        expected = lab.lwma_expected(port, next_height)
        template = lab.rpc(port, "get_block_template",
                           {"wallet_address": address, "reserve_size": 1})
        got = int(template["difficulty"])
        lab.require(int(template["height"]) == next_height,
                    f"{title}: next height mismatch {template['height']} != {next_height}")
        lab.require(got == expected,
                    f"{title} height {next_height}: computed {expected}, daemon {got}")
        lab.require(expected >= 1,
                    f"{title}: invalid zero-difficulty template")
        lab.mine(port, 1, address, nonce_base + index)
        block = lab.header(port, next_height)
        lab.require(int(block["major_version"]) == 17,
                    f"{title}: height {next_height} was not version 17")
        lab.require(int(block["difficulty"]) == expected,
                    f"{title}: block {next_height} difficulty {block['difficulty']} != {expected}")
        observed.append(expected)
        if index in (0, count // 2, count - 1):
            print(f"{title} height {next_height}: LWMA {expected} == block difficulty",
                  flush=True)
    lab.require(len(set(observed)) >= 2,
                f"{title}: difficulty did not change over {count} dynamic blocks")
    return observed


def main():
    daemon = lab.guard()
    source = (SOURCE / "src/cryptonote_core/feelcoin_treasury.h").read_text()
    m = re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"', source)
    lab.require(m is not None, "Public test payout address missing.")
    address = m.group(1)
    root = pathlib.Path(tempfile.mkdtemp(prefix="feelcoin-v17-retarget-"))
    print(f"Isolated test logs: {root}", flush=True)
    try:
        a = lab.start_node(daemon, root, "dynamic_a", lab.TEST_PORTS[0], fixed=False)
        b = lab.start_node(daemon, root, "dynamic_b", lab.TEST_PORTS[1], fixed=False)
        lab.require(a == b and a >= 122,
                    f"Bad or unequal seed blockchain: A={a}, B={b}")
        port_a, port_b = lab.TEST_PORTS[0][1], lab.TEST_PORTS[1][1]
        ancestor_a = lab.header(port_a, a - 1)["hash"]
        lab.require(ancestor_a == lab.header(port_b, b - 1)["hash"],
                    "Test copies do not have the same starting tip.")

        lab.say("Dynamic v17 difficulty: independently check every block")
        diffs_a = check_mine(port_a, 12, address, 103, "Node A")
        diffs_b = check_mine(port_b, 17, address, 5601, "Node B")
        old_tip = lab.current_tip(port_a)
        b_tip = lab.current_tip(port_b)
        lab.require(old_tip[1] != b_tip[1], "Competing branches identical")
        cumulative_a = int(lab.header(port_a, old_tip[0])["cumulative_difficulty"])
        cumulative_b = int(lab.header(port_b, b_tip[0])["cumulative_difficulty"])
        lab.require(cumulative_b > cumulative_a,
                    f"B must have more cumulative work: B={cumulative_b}, A={cumulative_a}")
        lab.say("Reorganize dynamic-difficulty branch B -> A")
        for height in range(a, b_tip[0] + 1):
            blob = lab.rpc(port_b, "get_block", {"height": height})["blob"]
            lab.rpc(port_a, "submit_block", [blob])
        new_tip = lab.current_tip(port_a)
        lab.require(new_tip == b_tip,
                    f"Reorg failed: A tip {new_tip}, B tip {b_tip}")
        lab.require(int(lab.header(port_a, b_tip[0])["cumulative_difficulty"]) ==
                    cumulative_b, "Reorg cumulative work differs")
        print(f"PASS: verified {len(diffs_a) + len(diffs_b)} dynamic LWMA blocks on two chains",
              flush=True)
        print(f"PASS: difficulty changed (A {min(diffs_a)}..{max(diffs_a)}, "
              f"B {min(diffs_b)}..{max(diffs_b)})", flush=True)
        print(f"PASS: dynamic-difficulty reorg succeeded at height {b_tip[0]}",
              flush=True)
        print("LIMIT: Both chains began from prior synthetic fixed-difficulty "
              "history; full 90-block dynamic-only history and adversarial "
              "timestamps remain untested.", flush=True)
    except Exception:
        print(f"\nFAIL: logs remain in {root}", file=sys.stderr, flush=True)
        for _, label in lab.PROCS:
            log = root / f"{label}.stdout"
            if log.is_file():
                print(f"\n--- {label} log tail ---", file=sys.stderr)
                print("\n".join(log.read_text(errors="replace").splitlines()[-25:]),
                      file=sys.stderr)
        raise
    finally:
        lab.stop_nodes()
        print(f"Artifacts: {root}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
