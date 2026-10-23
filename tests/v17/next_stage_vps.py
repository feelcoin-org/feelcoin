#!/usr/bin/env python3
"""Feelcoin v17 second-stage *isolated* VPS integration checks.

1. Two independent offline regtest daemons, competing v17 branches, reorg.
2. A separate daemon without --fixed-difficulty: check its LWMA result
   against an independent Python calculation and mine one v17 test block.

The seed database is from the successfully completed v17 fixed-diff smoke test.
It is synthetic, so this is NOT a full variable-difficulty-history replay.
"""
import json
import os
import pathlib
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def say(message):
    print("\n=== " + message + " ===", flush=True)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[2]
SEED_LAB = pathlib.Path(os.environ.get("V17_REUSE_LAB", ""))
TEST_PORTS = [(46180, 46181, 46182), (46280, 46281, 46282), (46380, 46381, 46382)]
PROCS = []
OUTPUTS = []


def cmd(*args):
    return subprocess.check_output(args, text=True).strip()


def guard():
    require(os.geteuid() != 0, "Run as unprivileged feelv17 user, never as root.")
    require(socket.gethostname().split(".")[0] == "vmi3643900",
            "This test is locked to the designated spare Contabo VPS.")
    require("156.67.29.237" in cmd("ip", "-4", "addr", "show"),
            "Spare VPS public IP not found.")
    require(cmd("git", "-C", str(SOURCE), "branch", "--show-current") ==
            "test/v17-isolated-regtest", "Wrong source branch.")
    require("std::make_pair(uint8_t(17), 120)" in
            (SOURCE / "src/cryptonote_core/cryptonote_core.cpp").read_text(),
            "Missing isolated v17 regtest activation.")
    mainnet = (SOURCE / "src/hardforks/hardforks.cpp").read_text()
    section = mainnet.split("mainnet_hard_forks", 1)[-1].split("};", 1)[0]
    require(not re.search(r"\{\s*17\s*,", section),
            "Mainnet fork schedule was modified; refusing.")
    require(str(SEED_LAB).startswith("/tmp/feelcoin-v17-regtest."),
            "Set V17_REUSE_LAB to the original isolated test lab.")
    require(SEED_LAB.is_dir() and not SEED_LAB.is_symlink() and
            SEED_LAB.stat().st_uid == os.geteuid(),
            "Original lab missing or not owned by test user.")
    require((SEED_LAB / "build/CMakeCache.txt").exists(),
            "Original CMake build missing.")
    cache = (SEED_LAB / "build/CMakeCache.txt").read_text()
    require(f"CMAKE_HOME_DIRECTORY:INTERNAL={SOURCE}" in cache,
            "Build belongs to another checkout.")
    require((SEED_LAB / "data").is_dir(), "Previous fakechain database missing.")
    for p in TEST_PORTS:
        for port in p:
            with socket.socket() as sock:
                try:
                    sock.bind(("127.0.0.1", port))
                except OSError as e:
                    raise RuntimeError(f"Test port {port} is occupied: {e}") from e
    for port in (35780, 35781, 35782):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError as e:
                raise RuntimeError(f"Production-like local port {port} is used: {e}") from e
    require(subprocess.run(["pgrep", "-x", "feelcoind"],
                           stdout=subprocess.DEVNULL).returncode != 0,
            "A Feelcoin daemon is already running.")
    daemon = SEED_LAB / "build/bin/feelcoind"
    require(daemon.is_file() and os.access(daemon, os.X_OK), "Compiled daemon missing.")
    return daemon


def rpc(port, method, params=None, timeout=90):
    data = json.dumps({"jsonrpc": "2.0", "id": "v17-next",
                       "method": method,
                       "params": {} if params is None else params}).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/json_rpc", data=data,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if payload.get("error"):
        raise RuntimeError(f"RPC {method} at {port}: {payload['error']}")
    result = payload.get("result", {})
    if result.get("status") not in (None, "OK"):
        raise RuntimeError(f"RPC {method} at {port}: {result}")
    return result


def start_node(daemon, root, label, ports, fixed=True):
    data = root / label / "data"
    shutil.copytree(SEED_LAB / "data", data)
    stdout_path = root / f"{label}.stdout"
    stream = stdout_path.open("w")
    OUTPUTS.append(stream)
    p2p, rpc_port, zmq_port = ports
    argv = [
        str(daemon), "--regtest", "--offline", "--keep-fakechain",
        "--non-interactive", "--data-dir", str(data),
        "--log-file", str(root / f"{label}.log"),
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpc_port),
        "--zmq-rpc-bind-ip", "127.0.0.1", "--zmq-rpc-bind-port", str(zmq_port),
        "--rpc-ssl", "disabled", "--no-igd",
        "--disable-dns-checkpoints", "--check-updates", "disabled",
    ]
    if fixed:
        argv += ["--fixed-difficulty", "1"]
    proc = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT,
                            start_new_session=True)
    PROCS.append((proc, label))
    for _ in range(60):
        if proc.poll() is not None:
            raise RuntimeError(f"{label}: daemon exited early with {proc.returncode}")
        try:
            info = rpc(rpc_port, "get_info", timeout=8)
            require(info.get("nettype") == "fakechain", "Not a fakechain!")
            return int(info["height"])
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(1)
    raise RuntimeError(f"{label}: offline daemon did not start")


def stop_nodes():
    for proc, _ in PROCS:
        if proc.poll() is None:
            proc.terminate()
    for proc, _ in PROCS:
        if proc.poll() is None:
            try:
                proc.wait(timeout=12)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    for f in OUTPUTS:
        f.close()


def header(port, height):
    return rpc(port, "get_block_header_by_height", {"height": height})["block_header"]


def mine(port, count, address, nonce):
    result = rpc(port, "generateblocks",
                 {"amount_of_blocks": count, "wallet_address": address,
                  "starting_nonce": nonce}, timeout=180)
    require(len(result["blocks"]) == count,
            f"Expected {count} generated blocks at {port}: {result}")
    return result


def current_tip(port):
    info = rpc(port, "get_info")
    height = int(info["height"]) - 1
    return height, header(port, height)["hash"]


def lwma_expected(port, next_height):
    # get_difficulty_for_next_block() uses the last 90+1 points.
    win = 90
    fields = [header(port, h) for h in range(next_height - win - 1, next_height)]
    require(len(fields) == win + 1, "Missing LWMA history.")
    timestamps = [int(h["timestamp"]) for h in fields]
    # Small synthetic fixed-diff chain: 64-bit field is sufficient.
    work = [int(h["cumulative_difficulty"]) for h in fields]
    prev = timestamps[0]
    weighted = 0
    for i, ts in enumerate(timestamps[1:], start=1):
        if ts > prev:
            solve = min(ts - prev, 720)
            prev = ts
        else:
            solve = 1
            prev = min(prev + 1, 2**64 - 1)
        weighted += i * solve
    weighted = max(weighted, max(1, win * win * 120 // 20))
    total_work = work[-1] - work[0]
    require(total_work > 0, "Cumulative work history invalid")
    result = total_work * (win + 1) * 120 // (2 * weighted)
    return max(result, 1)


def test_reorg(daemon, root, address):
    say("Two offline nodes: test v17 competing branches and reorganization")
    a_port, b_port = TEST_PORTS[0][1], TEST_PORTS[1][1]
    height_a = start_node(daemon, root, "node_a", TEST_PORTS[0], fixed=True)
    height_b = start_node(daemon, root, "node_b", TEST_PORTS[1], fixed=True)
    require(height_a == height_b and height_a > 120,
            f"Seed chain invalid or unequal: A={height_a}, B={height_b}")
    initial_hash = header(a_port, height_a - 1)["hash"]
    require(initial_hash == header(b_port, height_b - 1)["hash"],
            "Test nodes do not share the same ancestor.")
    mine(a_port, 2, address, 7)
    mine(b_port, 3, address, 9001)
    a_old = current_tip(a_port)
    b_tip = current_tip(b_port)
    require(a_old[1] != b_tip[1], "Two candidate branches are identical.")
    require(b_tip[0] == a_old[0] + 1, "B is not exactly one block longer than A.")
    print(f"A competing tip: height {a_old[0]}, {a_old[1][:16]}...",
          flush=True)
    print(f"B competing tip: height {b_tip[0]}, {b_tip[1][:16]}...",
          flush=True)

    for h in range(height_a, b_tip[0] + 1):
        blob = rpc(b_port, "get_block", {"height": h})["blob"]
        rpc(a_port, "submit_block", [blob])
        print(f"Forwarded valid competing block {h} B -> A", flush=True)
    a_new = current_tip(a_port)
    require(a_new == b_tip,
            f"Reorganization failed: A {a_new} != B {b_tip}")
    require(a_new[1] != a_old[1], "A did not change its canonical tip.")
    require(int(header(a_port, 120)["major_version"]) == 17,
            "V17 activation was lost during reorganization.")
    print("PASS: competing v17 branch accepted, heavier branch became canonical.",
          flush=True)


def test_dynamic(daemon, root, address):
    say("No fixed difficulty: independently verify v17 LWMA and mine one block")
    port = TEST_PORTS[2][1]
    height = start_node(daemon, root, "node_dynamic", TEST_PORTS[2], fixed=False)
    require(height > 120, f"No v17 history at dynamic node: {height}")
    expected = lwma_expected(port, height)
    template = rpc(port, "get_block_template",
                   {"wallet_address": address, "reserve_size": 1})
    reported = int(template["difficulty"])
    require(reported == expected,
            f"LWMA mismatch at height {height}: expected {expected}, daemon {reported}")
    require(int(template["height"]) == height, "Wrong template height.")
    print(f"Height {height} expected LWMA = {expected}; daemon = {reported}",
          flush=True)
    mine(port, 1, address, 801)
    result = header(port, height)
    require(int(result["major_version"]) == 17,
            "Mined block did not use v17.")
    require(int(result["difficulty"]) == expected,
            f"Mined block difficulty mismatch: {result['difficulty']} vs {expected}")
    print(f"PASS: v17 block mined at calculated LWMA difficulty {expected}.",
          flush=True)
    print("LIMIT: History was originally generated at fixed difficulty 1; "
          "this is a seeded integration check, not a fully dynamic-history replay.",
          flush=True)


def main():
    daemon = guard()
    source = (SOURCE / "src/cryptonote_core/feelcoin_treasury.h").read_text()
    m = re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"', source)
    require(m, "Public synthetic test address missing.")
    root = pathlib.Path(tempfile.mkdtemp(prefix="feelcoin-v17-next-"))
    print(f"Isolated artifacts: {root}", flush=True)
    try:
        test_reorg(daemon, root, m.group(1))
        stop_nodes()
        PROCS.clear()
        OUTPUTS.clear()
        test_dynamic(daemon, root, m.group(1))
        say("PASS: v17 second-stage isolated VPS integration checks")
    except Exception:
        print(f"\nFAILED: diagnostic logs retained in {root}", file=sys.stderr, flush=True)
        for _, label in PROCS:
            log = root / f"{label}.stdout"
            if log.is_file():
                print(f"\n--- {label} log tail ---", file=sys.stderr)
                print("\n".join(log.read_text(errors="replace").splitlines()[-20:]),
                      file=sys.stderr)
        raise
    finally:
        stop_nodes()
        print(f"Lab logs: {root}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
