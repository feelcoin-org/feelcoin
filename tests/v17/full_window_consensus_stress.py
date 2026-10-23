#!/usr/bin/env python3
"""v17 Stage 4: deterministic 90+ dynamic-block LWMA and timestamp stress.

Only for the dedicated offline Contabo test VPS. No network daemon, mining,
wallet or node is started. Compiles the actual production LWMA and timestamp
helpers as a standalone C++ probe and checks against an independent Python
reference using long simulated sequences. Does NOT replace consensus network
integration, genuine block replay, or security audit.
"""
import os
import pathlib
import random
import socket
import subprocess
import sys
import tempfile

SOURCE = pathlib.Path(__file__).resolve().parents[2]
UINT64 = (1 << 64) - 1
UINT128 = (1 << 128) - 1
TARGET = 120

CPP = r"""
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
#include <boost/multiprecision/cpp_int.hpp>
#include "cryptonote_basic/feelcoin_lwma.h"
#include "cryptonote_basic/feelcoin_timestamp_rules.h"
int main() {
  std::string mode;
  while (std::cin >> mode) {
    if (mode == "D") {
      size_t n = 0, target = 0, window = 0;
      if (!(std::cin >> n >> target >> window) || n > 10000) return 3;
      std::vector<uint64_t> times;
      std::vector<boost::multiprecision::uint128_t> work;
      times.reserve(n);
      work.reserve(n);
      for (size_t i = 0; i < n; ++i) {
        uint64_t timestamp;
        std::string c;
        if (!(std::cin >> timestamp >> c)) return 4;
        times.push_back(timestamp);
        try { work.emplace_back(c); }
        catch (...) { return 5; }
      }
      std::cout << cryptonote::next_difficulty_lwma(
        times, work, target, window) << "\n";
    } else if (mode == "T") {
      uint64_t block, now;
      unsigned version;
      if (!(std::cin >> block >> now >> version)) return 6;
      std::cout << (cryptonote::feelcoin_timestamp_within_future_limit(
        block, now, static_cast<uint8_t>(version)) ? "1" : "0") << "\n";
    } else {
      return 7;
    }
  }
}
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def guard():
    require(os.geteuid() != 0, "Do not run the test as root.")
    require(socket.gethostname().split(".")[0] == "vmi3643900",
            "Refusing: this is not the dedicated test VPS.")
    ip = subprocess.check_output(["ip", "-4", "addr", "show"], text=True)
    require("156.67.29.237" in ip, "Contabo test IP was not found.")
    branch = subprocess.check_output(
        ["git", "-C", str(SOURCE), "branch", "--show-current"], text=True).strip()
    require(branch == "test/v17-isolated-regtest", "Not on test-only branch.")
    require("std::make_pair(uint8_t(17), 120)" in
            (SOURCE / "src/cryptonote_core/cryptonote_core.cpp").read_text(),
            "Test activation schedule missing.")
    mainnet = (SOURCE / "src/hardforks/hardforks.cpp").read_text()
    section = mainnet.split("mainnet_hard_forks", 1)[-1].split("};", 1)[0]
    import re
    require(not re.search(r"\{\s*17\s*,", section),
            "Mainnet fork schedule modified; aborting.")
    require((SOURCE / "src/cryptonote_basic/feelcoin_lwma.h").exists(),
            "Real LWMA header is missing.")
    require((SOURCE / "src/cryptonote_basic/feelcoin_timestamp_rules.h").exists(),
            "Real timestamp helper is missing.")


def oracle(times, cumulative, target=TARGET, window=90):
    n = len(times)
    if (n != len(cumulative) or window == 0 or window > 120 or
            target == 0 or n <= window or
            target > UINT64 // (6 * window * window)):
        return 0
    first = n - window - 1
    if cumulative[-1] <= cumulative[first]:
        return 0
    previous = times[first]
    weighted = 0
    for i, stamp in enumerate(times[first + 1:], 1):
        if stamp > previous:
            delay = min(stamp - previous, 6 * target)
            previous = stamp
        else:
            delay = 1
            previous = min(previous + 1, UINT64)
        weighted += i * delay
    weighted = max(weighted, max(1, window * window * target // 20))
    result = (cumulative[-1] - cumulative[first]) * (window + 1) * target // (2 * weighted)
    if result > UINT128:
        return 0
    return max(result, 1)


def initial(window=90, start=1_800_000_000, work=1000):
    stamps = [start + 120 * i for i in range(window + 1)]
    cumulative = [(i + 1) * work for i in range(window + 1)]
    return stamps, cumulative


def record(cases, times, work, window=90, target=120):
    expected = oracle(times, work, target, window)
    cases.append(("D", list(times), list(work), target, window, expected))
    return expected


def run_trajectory(cases, label, durations, window=90, start=1_800_000_000,
                   initial_work=1000):
    times, cumulative = initial(window, start, initial_work)
    values = []
    for duration in durations:
        next_diff = record(cases, times, cumulative, window)
        require(0 < next_diff <= UINT128, label + ": simulated invalid retarget")
        times.append(max(0, min(UINT64, times[-1] + duration)))
        cumulative.append(cumulative[-1] + next_diff)
        require(cumulative[-1] <= UINT128, label + ": cumulative work overflow")
        values.append(next_diff)
    require(len(values) >= 91, label + ": fewer than 90 consecutive dynamic retargets")
    require(len(set(values)) > 1, label + ": difficulty never adjusted")
    print(f"  {label}: {len(values)} dynamic steps; diff {min(values)}..{max(values)}",
          flush=True)
    return values


def generate_cases():
    cases = []
    print("=== 90+ BLOCK DYNAMIC-HISTORY / LWMA STRESS ===", flush=True)
    a = run_trajectory(
        cases, "hashrate-shift: fast/slow/recovery",
        [120] * 105 + [60] * 75 + [240] * 100 + [120] * 105)
    require(max(a) > min(a), "Shift should change difficulty")
    b = run_trajectory(
        cases, "hashrate-shift: slow/fast/recovery",
        [120] * 105 + [240] * 100 + [60] * 75 + [120] * 105)
    require(max(b) > min(b), "Shift should change difficulty")
    rng = random.Random(20261023)
    run_trajectory(cases, "jitter/out-of-order timestamps",
                   [rng.choice([-600, -200, 0, 1, 12, 45, 120, 180, 720, 1300])
                    for _ in range(360)], start=1_800_000_000)
    run_trajectory(cases, "120-block custom window",
                   [120] * 110 + [75] * 105 + [180] * 105, window=120)
    # Large 128-bit work and out-of-order timestamps near the integer boundary.
    base = UINT64 - 10_000
    times = [base + 120 * i for i in range(80)] + [UINT64] * 11
    large = 1 << 111
    cumulative = [(i + 1) * large for i in range(91)]
    record(cases, times, cumulative)
    record(cases, [1000] * 91, cumulative)
    record(cases, [UINT64] * 91, cumulative)
    record(cases, [1000] * 90, cumulative)    # size mismatch
    record(cases, times, cumulative, window=121)
    record(cases, times, cumulative, target=0)
    record(cases, times, cumulative, window=0)
    record(cases, times, [cumulative[0]] * 91)
    bad = list(cumulative)
    bad[-1] = 0
    record(cases, times, bad)
    # Check only the newest data is used, even if huge older history exists.
    long_times, long_work = initial(window=120)
    long_times += [long_times[-1] + 120 * i for i in range(1, 150)]
    long_work += [long_work[-1] + 1000 * i for i in range(1, 150)]
    record(cases, long_times, long_work)
    ts = []
    print("=== TIMESTAMP POLICY / OVERFLOW STRESS ===", flush=True)
    fixed_now = 1_800_000_000
    for hf in (16, 17, 18):
        allowance = 7200 if hf == 16 else 1800
        for delta in (-7201, -1801, -1, 0, 1, 1799, 1800, 1801,
                      7199, 7200, 7201):
            candidate = fixed_now + delta
            ts.append(("T", candidate, fixed_now, hf,
                       int(candidate <= fixed_now + allowance)))
        for now in (0, 1, UINT64 - 8000, UINT64 - 1800,
                    UINT64 - 10, UINT64):
            ceiling = min(UINT64, now + allowance)
            for block in (0, 1, UINT64 - 8000, UINT64 - 1800,
                          UINT64 - 10, UINT64):
                ts.append(("T", block, now, hf, int(block <= ceiling)))
    print(f"Prepared {len(cases)} C++ difficulty vectors and {len(ts)} timestamp cases.",
          flush=True)
    return cases, ts


def main():
    guard()
    cases, ts_cases = generate_cases()
    with tempfile.TemporaryDirectory(prefix="feelcoin-v17-stage4-") as tmp:
        program = pathlib.Path(tmp) / "probe.cpp"
        exe = pathlib.Path(tmp) / "probe"
        program.write_text(CPP)
        print("=== COMPILE ACTUAL V17 CONSENSUS HELPERS ===", flush=True)
        subprocess.run(["g++", "-std=c++17", "-O2", "-I", str(SOURCE / "src"),
                        str(program), "-o", str(exe)], check=True)
        payload = []
        expected = []
        for mode, stamps, works, target, win, value in cases:
            payload.append(f"D {len(stamps)} {target} {win}\n")
            payload.extend(f"{t} {w}\n" for t, w in zip(stamps, works))
            expected.append(str(value))
        for _, block, now, hf, expected_value in ts_cases:
            payload.append(f"T {block} {now} {hf}\n")
            expected.append(str(expected_value))
        print("=== CROSS-CHECK C++ vs INDEPENDENT PYTHON ORACLE ===", flush=True)
        result = subprocess.run([str(exe)], input="".join(payload), text=True,
                                capture_output=True, timeout=120)
        require(result.returncode == 0, f"C++ probe failed: {result.stderr}")
        outputs = result.stdout.splitlines()
        require(len(outputs) == len(expected),
                f"Output count mismatch: got {len(outputs)}, expected {len(expected)}")
        for i, (actual, want) in enumerate(zip(outputs, expected)):
            require(actual == want,
                    f"Consensus result mismatch at vector {i}: C++={actual}, Python={want}")
    print(f"PASS: {len(cases)} production C++ LWMA vectors match Python reference.",
          flush=True)
    print(f"PASS: {len(ts_cases)} production C++ timestamp policy cases match Python reference.",
          flush=True)
    print("PASS: multiple >90-block simulated dynamic retarget histories.", flush=True)
    print("LIMIT: synthetic histories are not 90 consecutively mined blocks; "
          "no mainnet replay or network adversarial testing done.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
