#!/usr/bin/env python3
"""Feelcoin v17 Stage 8: one-shot mixed v16/v17 upgrade rehearsal.

Everything runs on a dedicated spare Contabo machine on loopback in FAKECHAIN
regtest. Builds genuine main-branch v16 binary at a pinned SHA (if necessary).
Mines a pre-activation v16 chain, boots old v16 and candidate v17 daemons on
the same history, validates pre-fork synchronization, v17 fork and rejection by
old v16, and rejection of old v16 blocks by v17 peers. No production changes.
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error

import next_stage_vps as lab

SOURCE = pathlib.Path(__file__).resolve().parents[2]
ROOT = pathlib.Path("/home/feelv17/feelcoin-v17-mixed-lab")
REF_SRC = ROOT / "source-v16"
REF_BUILD = ROOT / "build-v16"
REF_BIN = REF_BUILD / "bin/feelcoind"
PINNED_BASE = "c41b1cf5f15ed150c6e070d8598503aab920670e"
PINNED_V17_BIN_SHA256 = "5ac57edabd277287a257ac4783f931ef63a94249433af47fd372963d02c599bd"
MARKER_TEXT = "Feelcoin v17 isolated mixed-version rehearsal. No mainnet wallets.\n"
PORT_OLD, PORT_NEW_A, PORT_NEW_B = lab.TEST_PORTS


def must(value, why):
    if not value:
        raise RuntimeError(why)


def cmd(*args):
    return subprocess.check_output(args, text=True).strip()


def logged(command, logfile, timeout=3600):
    print("RUN:", " ".join(str(a) for a in command[:4]), "...", flush=True)
    with (ROOT / logfile).open("a") as output:
        try:
            subprocess.run(command, cwd=str(ROOT), stdout=output,
                           stderr=subprocess.STDOUT, check=True, timeout=timeout)
        except Exception:
            lines = (ROOT / logfile).read_text(errors="replace").splitlines()[-30:]
            print("\n".join(lines), file=sys.stderr, flush=True)
            raise


def prepare():
    candidate = lab.guard()  # Guard spare host, fakechain schedule, all ports & daemon absence
    must(hashlib.sha256(candidate.read_bytes()).hexdigest() == PINNED_V17_BIN_SHA256,
         "v17 candidate binary differs from previously validated Stage 1–7 binary")
    old_cfg = SOURCE / "src/cryptonote_config.h"
    must(old_cfg.exists(), "Candidate consensus network configuration not found")
    must(not ROOT.is_symlink(), "Refusing lab directory symlink")
    if not ROOT.exists():
        ROOT.mkdir(mode=0o700)
        (ROOT / ".feelcoin-v17-mixed-lab").write_text(MARKER_TEXT)
    must(ROOT.is_dir() and ROOT.stat().st_uid == os.geteuid(),
         "Mixed lab owner mismatch")
    must(shutil.disk_usage(ROOT).free > 6 * 1024**3,
         "Need at least 6GB free disk to safely build old v16 and run tests")
    must((ROOT / ".feelcoin-v17-mixed-lab").read_text() == MARKER_TEXT,
         "Mixed lab ownership marker missing")

    if not REF_SRC.exists():
        print("=== Prepare pinned v16 reference source (never production) ===",
              flush=True)
        logged(["git", "-C", str(SOURCE), "fetch", "--depth=1", "origin",
                PINNED_BASE], "baseline-fetch.log", timeout=900)
        logged(["git", "-C", str(SOURCE), "worktree", "add", "--detach",
                str(REF_SRC), PINNED_BASE], "baseline-worktree.log", timeout=120)
    must(not REF_SRC.is_symlink(), "v16 source symlink refused")
    must(cmd("git", "-C", str(REF_SRC), "rev-parse", "HEAD") == PINNED_BASE,
         "v16 reference source is not pinned main-branch baseline")
    must(cmd("git", "-C", str(SOURCE), "branch", "--show-current") ==
         "test/v17-isolated-regtest", "Candidate test source branch unexpectedly changed")

    old_forks = (REF_SRC / "src/hardforks/hardforks.cpp").read_text()
    for version, label in [(old_forks, "v16 baseline"),
                           ((SOURCE / "src/hardforks/hardforks.cpp").read_text(),
                            "candidate production schedule")]:
        part = version.split("mainnet_hard_forks", 1)[-1].split("};", 1)[0]
        must(not re.search(r"\{\s*17\s*,", part),
             f"{label}: mainnet v17 activation found — refusing")
    old_core = (REF_SRC / "src/cryptonote_core/cryptonote_core.cpp").read_text()
    must("std::make_pair(0, 0)" in old_core and
         "std::make_pair(uint8_t(17), 120)" not in old_core,
         "v16 baseline has non-v16 isolated regtest fork schedule")
    new_cfg = old_cfg.read_text()
    base_cfg = (REF_SRC / "src/cryptonote_config.h").read_text()
    for field in ("GENESIS_TX", "GENESIS_NONCE", "NETWORK_ID"):
        if field == "GENESIS_TX":
            old_val = re.search(r'GENESIS_TX\s*=\s*"([^"]+)"', base_cfg)
            new_val = re.search(r'GENESIS_TX\s*=\s*"([^"]+)"', new_cfg)
        elif field == "GENESIS_NONCE":
            old_val = re.search(r"GENESIS_NONCE\s*=\s*(\d+)", base_cfg)
            new_val = re.search(r"GENESIS_NONCE\s*=\s*(\d+)", new_cfg)
        else:
            old_val = re.search(r"NETWORK_ID\s*=\s*\{\s*\{([^}]*)\}", base_cfg)
            new_val = re.search(r"NETWORK_ID\s*=\s*\{\s*\{([^}]*)\}", new_cfg)
        must(old_val and new_val and old_val.group(1) == new_val.group(1),
             f"Candidate and pinned v16 differ on {field}; cannot conduct mixed test")

    if not REF_BIN.is_file():
        print("=== Build pinned v16 daemon once, outside all live installations ===",
              flush=True)
        logged(["git", "-C", str(REF_SRC), "submodule", "update",
                "--init", "--recursive", "--jobs", "2"],
               "baseline-submodules.log", timeout=1800)
        logged(["cmake", "-S", str(REF_SRC), "-B", str(REF_BUILD),
                "-DARCH=default", "-DCMAKE_BUILD_TYPE=Release",
                "-DBUILD_TESTS=OFF", "-DUSE_DEVICE_TREZOR=OFF"],
               "baseline-configure.log", timeout=450)
        logged(["cmake", "--build", str(REF_BUILD), "--target", "daemon",
                "--parallel", "2"], "baseline-build.log", timeout=5400)
    must(REF_BIN.is_file() and os.access(REF_BIN, os.X_OK),
         "Expected compiled baseline v16 daemon not found")
    print("PASS: matched v16 and v17 genesis, network ID, and mainnet v16 schedule",
          flush=True)
    print("v16 reference sha256:", hashlib.sha256(REF_BIN.read_bytes()).hexdigest(),
          flush=True)
    print("v17 candidate sha256:", PINNED_V17_BIN_SHA256, flush=True)
    return REF_BIN, candidate


def rpc(port, method, params=None, timeout=100):
    return lab.rpc(port, method, params, timeout=timeout)


def start(binary, data, label, ports, peers=(), offline=False):
    p2p, rpcport, _ = ports
    path = ROOT / "chain" / label
    path.mkdir(parents=True, exist_ok=True)
    logfile = ROOT / f"{label}.daemon.log"
    stdout = (ROOT / f"{label}.stdout").open("a")
    lab.OUTPUTS.append(stdout)
    args = [
        str(binary), "--regtest", "--keep-fakechain", "--fixed-difficulty", "1",
        "--non-interactive", "--data-dir", str(data), "--log-file", str(logfile),
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpcport),
        "--rpc-ssl", "disabled", "--no-zmq", "--no-igd",
        "--hide-my-port", "--disable-dns-checkpoints",
        "--check-updates", "disabled", "--max-concurrency", "2",
    ]
    if offline:
        args += ["--offline"]
    else:
        args += ["--allow-local-ip", "--in-peers", "3", "--out-peers", "2"]
        for peer_port in peers:
            args += ["--add-exclusive-node", f"127.0.0.1:{peer_port}"]
    process = subprocess.Popen(args, stdout=stdout, stderr=subprocess.STDOUT,
                               start_new_session=True)
    lab.PROCS.append((process, label))
    for _ in range(70):
        must(process.poll() is None,
             f"{label}: daemon exited, see {logfile}")
        try:
            info = rpc(rpcport, "get_info", timeout=6)
            must(info["nettype"] == "fakechain",
                 f"{label}: daemon unexpectedly on a live network")
            return
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(1)
    raise RuntimeError(f"{label}: daemon RPC startup timeout; see {logfile}")


def wait_for(predicate, reason, seconds=150):
    start_time = time.monotonic()
    while time.monotonic() - start_time < seconds:
        for p, label in lab.PROCS:
            must(p.poll() is None, f"{label}: exited unexpectedly")
        if predicate():
            return
        time.sleep(2)
    raise RuntimeError(reason)


def current_height(port):
    return lab.current_tip(port)[0]


def peer_counts(port):
    info = rpc(port, "get_info", timeout=8)
    incoming = int(info.get("incoming_connections_count", 0))
    outgoing = int(info.get("outgoing_connections_count", 0))
    return incoming, outgoing


def mixed_peers_ready():
    old_in, old_out = peer_counts(PORT_OLD[1])
    a_in, a_out = peer_counts(PORT_NEW_A[1])
    b_in, b_out = peer_counts(PORT_NEW_B[1])
    # Mutually dialing nodes may keep only incoming connections.
    # Three-node exclusive topology: old <-> A <-> B.
    return (old_in + old_out >= 1 and
            a_in + a_out >= 2 and
            b_in + b_out >= 1)


def print_peer_diagnostics():
    for name, port in (("old_v16", PORT_OLD[1]),
                       ("new_v17_a", PORT_NEW_A[1]),
                       ("new_v17_b", PORT_NEW_B[1])):
        try:
            incoming, outgoing = peer_counts(port)
            print(f"  {name}: incoming={incoming}, outgoing={outgoing}",
                  flush=True)
            connections = rpc(port, "get_connections", timeout=8)
            for connection in connections.get("connections", []):
                print(f"    peer={connection.get('peer_id', '?')} "
                      f"address={connection.get('address', '?')} "
                      f"incoming={connection.get('incoming', '?')}",
                      flush=True)
        except Exception as exc:
            print(f"  {name}: peer diagnostics unavailable: {exc}", flush=True)


def prove_rejection(port, blob, expected_tip):
    try:
        rpc(port, "submit_block", [blob], timeout=40)
    except RuntimeError as exc:
        must(str(exc).startswith(f"RPC submit_block at {port}: "),
             f"Unexpected RPC test failure: {exc}")
    else:
        raise RuntimeError("v17 daemon accepted obsolete v16 block after activation")
    must(lab.current_tip(port) == expected_tip,
         "Obsolete v16 block changed canonical v17 chain tip")


def run_mixed(old, new):
    source = (SOURCE / "src/cryptonote_core/feelcoin_treasury.h").read_text()
    a = re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"', source)
    must(a, "Synthetic public test mining address missing")
    payout = a.group(1)
    path = ROOT / "chain"
    path.mkdir(exist_ok=True)
    common = path / "v16_seed"
    old_seed = common / "data"
    old_seed.mkdir(parents=True, exist_ok=True)
    need_seed = not (ROOT / "v16_seed_119.ok").exists()
    if need_seed:
        print("=== Generate 119 genuine v16 fakechain blocks ===", flush=True)
        start(old, old_seed, "v16_seed", PORT_OLD, offline=True)
        while current_height(PORT_OLD[1]) < 119:
            h = current_height(PORT_OLD[1])
            count = min(20, 119 - h)
            lab.mine(PORT_OLD[1], count, payout, 30000 + h)
            print(f"  v16 baseline height {current_height(PORT_OLD[1])}", flush=True)
        must(current_height(PORT_OLD[1]) == 119,
             "Baseline did not end at height 119")
        must(int(lab.header(PORT_OLD[1], 119)["major_version"]) == 16,
             "Baseline's 119th block was not v16")
        for height in (1, 60, 118, 119):
            must(int(lab.header(PORT_OLD[1], height)["major_version"]) == 16,
                 f"Baseline unexpectedly activated v17 at {height}")
        lab.stop_nodes()
        lab.PROCS.clear()
        lab.OUTPUTS.clear()
        (ROOT / "v16_seed_119.ok").write_text(
            lab.cmd("git", "-C", str(REF_SRC), "rev-parse", "HEAD") + "\n")
    else:
        must((ROOT / "v16_seed_119.ok").read_text().strip() == PINNED_BASE,
             "Seed reference hash mismatch")
        must(old_seed.is_dir(), "Seed data missing")
    print("PASS: authentic pinned-v16 test history through height 119",
          flush=True)

    import tempfile
    run_root = pathlib.Path(tempfile.mkdtemp(prefix="mixed-run-", dir=ROOT))
    v16_data = run_root / "old_v16" / "data"
    new_a_data = run_root / "new_v17_a" / "data"
    new_b_data = run_root / "new_v17_b" / "data"
    # A new uniquely named fakechain each run allows safe recovery after a
    # failed test, without deleting any existing blockchain directory.
    for d in (v16_data, new_a_data, new_b_data):
        shutil.copytree(old_seed, d)
    print(f"Fresh isolated chain copies: {run_root}", flush=True)

    print("=== Boot original v16 plus two upgraded-v17 peers ===", flush=True)
    start(old, v16_data, "old_v16", PORT_OLD, peers=(PORT_NEW_A[0],))
    start(new, new_a_data, "new_v17_a", PORT_NEW_A,
          peers=(PORT_OLD[0], PORT_NEW_B[0]))
    start(new, new_b_data, "new_v17_b", PORT_NEW_B,
          peers=(PORT_NEW_A[0],))
    for p in (PORT_OLD[1], PORT_NEW_A[1], PORT_NEW_B[1]):
        must(current_height(p) == 119,
             f"Node RPC port {p} not at pre-fork height 119")
    try:
        wait_for(mixed_peers_ready,
                 "Old/new P2P handshake before fork did not connect",
                 seconds=180)
    except Exception:
        print("=== P2P handshake failure diagnostics ===", flush=True)
        print_peer_diagnostics()
        raise
    print_peer_diagnostics()
    print("PASS: v16 and v17 nodes share identical pre-fork tip and P2P links",
          flush=True)

    print("=== Upgrade-side v17 activation and network synchronization ===",
          flush=True)
    lab.mine(PORT_NEW_A[1], 3, payout, 82002)
    upgraded_tip = lab.current_tip(PORT_NEW_A[1])
    must(upgraded_tip[0] == 122 and
         int(lab.header(PORT_NEW_A[1], 120)["major_version"]) == 17,
         "New candidate failed to activate v17 exactly at block 120")
    wait_for(lambda: lab.current_tip(PORT_NEW_B[1]) == upgraded_tip,
             "Two v17 peers failed to propagate/synchronize post-fork chain",
             seconds=180)
    # Give the old node time to process new P2P announcements.
    time.sleep(8)
    must(current_height(PORT_OLD[1]) == 119,
         "Old v16 node unexpectedly accepted v17 chain after height 119")
    print("PASS: v17 candidates converge on block 122, old v16 refuses v17",
          flush=True)

    print("=== Check old-v16 competing block rejection by v17 network ===",
          flush=True)
    lab.mine(PORT_OLD[1], 1, payout, 45111)
    must(current_height(PORT_OLD[1]) == 120 and
         int(lab.header(PORT_OLD[1], 120)["major_version"]) == 16,
         "Old v16 node did not stay on its incompatible legacy fork")
    legacy_blob = rpc(PORT_OLD[1], "get_block", {"height": 120})["blob"]
    prove_rejection(PORT_NEW_A[1], legacy_blob, upgraded_tip)
    time.sleep(8)
    must(lab.current_tip(PORT_NEW_B[1]) == upgraded_tip,
         "Second v17 node followed incompatible legacy fork")
    print("PASS: v17 rejected old-v16 block at activation height; no chain split among upgrades",
          flush=True)

    print("=== Recheck P2P propagation post activation ===", flush=True)
    lab.mine(PORT_NEW_B[1], 2, payout, 99123)
    final_tip = lab.current_tip(PORT_NEW_B[1])
    wait_for(lambda: lab.current_tip(PORT_NEW_A[1]) == final_tip,
             "v17 peers lost P2P propagation after mixed-version partition",
             seconds=180)
    must(current_height(PORT_OLD[1]) == 120,
         "Old node unexpectedly followed v17 after fork")
    print(f"PASS: two v17 nodes agree at height {final_tip[0]}, legacy v16 "
          f"remains at height 120", flush=True)

    print("=== Complete treasury activation and RandomX seed epoch rehearsal ===",
          flush=True)
    # The real 2% treasury rule starts at height 590, independently from
    # the v17 test-fork height 120. Mine up to 591 with fixed-difficulty 1:
    # validates the RandomX seed transition at 512 and treasury enforcement
    # on both candidate daemons without any mainnet mining.
    while current_height(PORT_NEW_B[1]) < 591:
        h = current_height(PORT_NEW_B[1])
        blocks = min(20, 591 - h)
        lab.mine(PORT_NEW_B[1], blocks, payout, 120000 + h)
        if current_height(PORT_NEW_B[1]) % 100 < 20:
            print(f"  verified synthetic v17 height {current_height(PORT_NEW_B[1])}",
                  flush=True)
    final_tip = lab.current_tip(PORT_NEW_B[1])
    wait_for(lambda: lab.current_tip(PORT_NEW_A[1]) == final_tip,
             "v17 upgraded peers failed to converge through treasury activation",
             seconds=240)
    must(current_height(PORT_OLD[1]) == 120,
         "Obsolete node unexpectedly followed new v17 test chain")
    def outputs(height):
        raw = rpc(PORT_NEW_B[1], "get_block", {"height": height})
        block = json.loads(raw["json"])
        values = [int(item["amount"]) for item in block["miner_tx"]["vout"]]
        reported = int(lab.header(PORT_NEW_B[1], height)["reward"])
        must(sum(values) == reported,
             f"Coinbase output sum mismatch at height {height}")
        return values
    pre = outputs(589)
    active = outputs(590)
    post = outputs(591)
    must(len(pre) == 1 and len(active) == 2 and len(post) == 2,
         "Treasury activation must switch exactly at block 590")
    for height, amounts in ((590, active), (591, post)):
        expected_treasury = sum(amounts) * 2 // 100
        must(amounts[1] == expected_treasury,
             f"Height {height} treasury output not 2% of block subsidy")
        must(amounts[0] > amounts[1],
             f"Height {height} miner must receive more than treasury")
    print("PASS: v17 nodes synchronized through RandomX seed epoch height 512",
          flush=True)
    print("PASS: height 589 one coinbase output; heights 590/591 two outputs",
          flush=True)
    print("PASS: consensus treasury allocation exactly 2% of fakechain subsidy",
          flush=True)
    print("PASS: Stage 8 mixed-version activation, P2P and economics checks",
          flush=True)
    print("LIMIT: all on isolated two-node/legacy fakechain with fixed difficulty 1.",
          flush=True)
    print("NO MAINNET ACTIVATION, NO NODE UPGRADE, WINDOWS TEST DELEGATED TO USER.",
          flush=True)
    report = {
        "test": "Stage 8 pinned main-v16 vs regtest-v17 upgrade rehearsal",
        "baseline_commit": PINNED_BASE,
        "reference_binary_sha256": hashlib.sha256(old.read_bytes()).hexdigest(),
        "candidate_binary_sha256": PINNED_V17_BIN_SHA256,
        "activation_height": 120,
        "upgraded_tip_height": final_tip[0],
        "upgraded_tip_hash": final_tip[1],
        "legacy_tip_height": current_height(PORT_OLD[1]),
        "passed": True, "production_affected": False,
        "mainnet_activated": False,
    }
    (ROOT / "stage8-result.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Report:", ROOT / "stage8-result.json", flush=True)


def main():
    try:
        old, new = prepare()
        run_mixed(old, new)
    except Exception:
        for f in sorted(ROOT.glob("*.daemon.log")):
            try:
                print(f"--- {f.name} last lines ---", file=sys.stderr)
                print("\n".join(f.read_text(errors="replace").splitlines()[-12:]),
                      file=sys.stderr)
            except Exception:
                pass
        raise
    finally:
        lab.stop_nodes()
        print("All isolated test daemons stopped.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("STAGE 8 FAILED:", str(e), file=sys.stderr, flush=True)
        sys.exit(1)
