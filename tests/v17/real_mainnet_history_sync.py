#!/usr/bin/env python3
"""v17 Stage 6: REAL mainnet block-history compatibility sync on spare VPS.

Uses the already-verified v17-candidate binary, whose MAINNET hardfork schedule
remains v16. Downloads/validates real existing mainnet blocks into a NEW,
isolated database on spare Contabo. Connects exclusively to Node1 by P2P.
Never touches a production service, wallet, or database. Does not test activation
of v17 on mainnet; that requires a separate coordinated fork test.
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request

SOURCE = pathlib.Path(__file__).resolve().parents[2]
LAB_BINARY = pathlib.Path("/tmp/feelcoin-v17-regtest.11Zyg4mk/build/bin/feelcoind")
KNOWN_SHA256 = "5ac57edabd277287a257ac4783f931ef63a94249433af47fd372963d02c599bd"
MAINNET_DATA = pathlib.Path("/home/feelv17/feelcoin-v17-mainnet-replay")
MARKER = ".v17_compat_owned_by_lab"
PEER = "node1.feelcoin.org"
PEER_PORT = 35780
P2P_PORT = 46480
RPC_PORT = 46481
LIMIT_SECONDS = 1800
proc = None


def require(test, text):
    if not test:
        raise RuntimeError(text)


def rpc(method, params=None):
    request = urllib.request.Request(
        f"http://127.0.0.1:{RPC_PORT}/json_rpc",
        data=json.dumps({"jsonrpc": "2.0", "id": "replay",
                         "method": method,
                         "params": params if params is not None else {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=8) as result:
        body = json.load(result)
    require("error" not in body, f"RPC {method} error: {body['error']}")
    return body["result"]


def validate_environment():
    require(os.geteuid() != 0, "Run only as unprivileged feelv17, not root")
    require(socket.gethostname().split(".")[0] == "vmi3643900",
            "Not the spare VPS vmi3643900")
    addr = subprocess.check_output(["ip", "-4", "addr", "show"], text=True)
    require("156.67.29.237" in addr, "Dedicated test VPS IPv4 does not match")
    branch = subprocess.check_output(
        ["git", "-C", str(SOURCE), "branch", "--show-current"],
        text=True).strip()
    require(branch == "test/v17-isolated-regtest", "Wrong isolated test checkout")
    src_hfs = (SOURCE / "src/hardforks/hardforks.cpp").read_text()
    mainnet = src_hfs.split("mainnet_hard_forks[]", 1)[-1].split("};", 1)[0]
    require(not re.search(r"\{\s*17\s*,", mainnet),
            "Mainnet v17 fork unexpectedly scheduled! Refusing.")
    regtest = (SOURCE / "src/cryptonote_core/cryptonote_core.cpp").read_text()
    require("std::make_pair(uint8_t(17), 120)" in regtest,
            "Test-only checkout no longer matches audited source.")
    require(LAB_BINARY.is_file() and os.access(LAB_BINARY, os.X_OK),
            "Previously verified test binary unavailable")
    digest = hashlib.sha256(LAB_BINARY.read_bytes()).hexdigest()
    require(digest == KNOWN_SHA256, "Binary checksum mismatch: cannot replay")
    require(not subprocess.run(["pgrep", "-x", "feelcoind"], check=False,
                               stdout=subprocess.DEVNULL).returncode == 0,
            "Another feelcoind is running on the spare VPS. Refusing.")
    for port in (P2P_PORT, RPC_PORT):
        with socket.socket() as check:
            check.bind(("127.0.0.1", port))
    require(shutil.disk_usage("/home/feelv17").free > 5 * 1024**3,
            "Insufficient disk space for safe real mainnet replay (need 5GB free)")
    require(MAINNET_DATA.parent.is_dir(), "Spare home directory not found")
    require(not MAINNET_DATA.is_symlink(), "Replay data directory is symlink")
    if not MAINNET_DATA.exists():
        MAINNET_DATA.mkdir(mode=0o700)
        (MAINNET_DATA / MARKER).write_text("feelcoin stage 6 dedicated isolated mainnet replay\n")
    require(MAINNET_DATA.is_dir(), "Replay path is not directory")
    require((MAINNET_DATA / MARKER).read_text() ==
            "feelcoin stage 6 dedicated isolated mainnet replay\n",
            "Replay data directory not tagged by Stage 6. Refusing.")
    require(MAINNET_DATA.stat().st_uid == os.geteuid(), "Directory owner mismatch")
    print("PASS: verified binary SHA256", digest, flush=True)
    print("PASS: v17 is not scheduled for mainnet; production paths untouched", flush=True)
    print("Dedicated replay database:", MAINNET_DATA, flush=True)


def check_network():
    try:
        with socket.create_connection((PEER, PEER_PORT), timeout=8):
            pass
    except OSError as exc:
        raise RuntimeError(f"Node1 P2P {PEER}:{PEER_PORT} unavailable: {exc}")
    print(f"PASS: Node1 P2P {PEER}:{PEER_PORT} reachable", flush=True)


def verify_history(top):
    require(top >= 500, f"Only {top} blocks synced; too little real history")
    candidates = {1, 2, 119, 120, top, top - 1}
    candidates.update(max(1, round((top - 1) * k / 25)) for k in range(1, 26))
    results = []
    for height in sorted(candidates):
        hdr = rpc("get_block_header_by_height", {"height": height})["block_header"]
        require(int(hdr["major_version"]) == 16,
                f"Historical v16 mismatch at height {height}")
        parent = rpc("get_block_header_by_height",
                     {"height": height - 1})["block_header"]
        require(hdr["prev_hash"] == parent["hash"],
                f"Historical parent hash mismatch at height {height}")
        require(int(hdr["cumulative_difficulty"]) >
                int(parent["cumulative_difficulty"]),
                f"Non-increasing work at height {height}")
        results.append((height, hdr["hash"]))
    print(f"PASS: {len(results)} sampled real mainnet block headers "
          "have v16 version, parent linkage and increasing cumulative work",
          flush=True)
    for index in (0, len(results) // 2, -1):
        h, hash_value = results[index]
        print(f"  Mainnet block {h}: {hash_value}", flush=True)


def run():
    global proc
    validate_environment()
    check_network()
    log_path = MAINNET_DATA / "replay-daemon.log"
    with log_path.open("a") as logfile:
        args = [
            str(LAB_BINARY), "--non-interactive",
            "--data-dir", str(MAINNET_DATA),
            "--log-file", str(MAINNET_DATA / "replay-core.log"),
            "--log-level", "0",
            "--p2p-bind-ip", "127.0.0.1",
            "--p2p-bind-port", str(P2P_PORT),
            "--rpc-bind-ip", "127.0.0.1",
            "--rpc-bind-port", str(RPC_PORT),
            "--rpc-ssl", "disabled",
            "--no-zmq", "--no-igd", "--hide-my-port",
            "--in-peers", "0", "--out-peers", "1",
            "--add-exclusive-node", f"{PEER}:{PEER_PORT}",
            "--check-updates", "disabled",
            "--disable-dns-checkpoints",
            "--max-concurrency", "2",
        ]
        print("=== STAGE 6: LIVE MAINNET HISTORY REPLAY (NO FORK ACTIVATION) ===",
              flush=True)
        print("Peer: Node1 only; local-only RPC; no mining; no wallet use", flush=True)
        proc = subprocess.Popen(args, stdout=logfile, stderr=subprocess.STDOUT,
                                start_new_session=True)
        started = time.monotonic()
        last_print = 0
        errors = 0
        while time.monotonic() - started <= LIMIT_SECONDS:
            require(proc.poll() is None,
                    f"Replay daemon exited ({proc.returncode}); "
                    f"inspect {log_path} and replay-core.log")
            require(shutil.disk_usage(MAINNET_DATA).free > 1024**3,
                    "Free disk space dropped under 1GB; stopping safely.")
            try:
                stats = rpc("get_info")
                nettype = stats.get("nettype")
                require(nettype == "mainnet",
                        f"Expected mainnet, got {nettype!r}!")
                height = int(stats["height"]) - 1
                target = int(stats.get("target_height", 0))
                outgoing = int(stats.get("outgoing_connections_count", 0))
                synced = bool(stats.get("synchronized", False))
                if time.monotonic() - last_print >= 25:
                    print(f"SYNC height={height}, target={target}, "
                          f"outgoing_peers={outgoing}, synchronized={synced}",
                          flush=True)
                    last_print = time.monotonic()
                if synced and outgoing > 0 and height >= 500 and (
                        target == 0 or height >= target - 1):
                    verify_history(height)
                    print(f"PASS: real mainnet historical block validation "
                          f"through height {height}; v17 mainnet still NOT active",
                          flush=True)
                    print("LIMIT: this proves pre-fork chain compatibility only, "
                          "not live v17 activation or peer-partition recovery.",
                          flush=True)
                    return
                errors = 0
            except (OSError, ValueError, KeyError) as exc:
                errors += 1
                if errors >= 18:
                    raise RuntimeError(f"Daemon RPC unresponsive: {exc}")
            time.sleep(5)
        print(f"INCOMPLETE: sync time limit reached after {LIMIT_SECONDS}s; "
              f"preserved database for resumption at {MAINNET_DATA}", flush=True)
        print("Re-run this Stage 6 command to resume, not restart.", flush=True)


if __name__ == "__main__":
    failed = False
    try:
        run()
    except Exception as exc:
        failed = True
        print(f"STAGE 6 ERROR: {exc}", file=sys.stderr, flush=True)
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        print("Stage 6 daemon closed; production remains unchanged.", flush=True)
    if failed:
        sys.exit(1)
