#!/usr/bin/env python3
"""Feelcoin v17 Stage 7: isolated REAL P2P propagation, partition/rejoin, reorg.

Uses the previously built regtest-only candidate on the dedicated spare VPS.
All peer and RPC sockets bind to loopback. Nodes cannot contact mainnet.
Neither node uses a real wallet or changes existing chains. Windows is separate.
"""
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error

import next_stage_vps as lab

ROOT_SOURCE = pathlib.Path(__file__).resolve().parents[2]
PORTS_A, PORTS_B = lab.TEST_PORTS[:2]


def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def start(daemon, base, name, ports, *, connected, copy_seed=False):
    d = base / name / "data"
    if copy_seed:
        shutil.copytree(lab.SEED_LAB / "data", d)
    need(d.is_dir() and not d.is_symlink(),
         f"{name}: isolated chain directory missing or symlink")
    p2p, rpcport, _ = ports
    stdout = (base / f"{name}-{'p2p' if connected else 'partition'}.stdout").open("a")
    lab.OUTPUTS.append(stdout)
    args = [
        str(daemon), "--regtest", "--keep-fakechain", "--fixed-difficulty", "1",
        "--non-interactive", "--data-dir", str(d),
        "--log-file", str(base / f"{name}-{'p2p' if connected else 'partition'}.log"),
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpcport),
        "--rpc-ssl", "disabled", "--no-zmq", "--no-igd",
        "--hide-my-port", "--disable-dns-checkpoints",
        "--check-updates", "disabled", "--max-concurrency", "2",
    ]
    if connected:
        # Local-only P2P; no DNS seeds, no remote peers or listening interfaces.
        peer_port = PORTS_B[0] if name == "node_a" else PORTS_A[0]
        args += [
            "--allow-local-ip", "--in-peers", "2", "--out-peers", "1",
            "--add-exclusive-node", f"127.0.0.1:{peer_port}",
        ]
    else:
        args += ["--offline"]
    p = subprocess.Popen(args, stdout=stdout, stderr=subprocess.STDOUT,
                         start_new_session=True)
    lab.PROCS.append((p, f"{name}-{'p2p' if connected else 'partition'}"))
    for _ in range(60):
        need(p.poll() is None, f"{name}: daemon stopped with code {p.returncode}")
        try:
            info = lab.rpc(rpcport, "get_info", timeout=5)
            need(info.get("nettype") == "fakechain",
                 f"{name}: unexpected network, refusing")
            return info
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(1)
    raise RuntimeError(f"{name}: RPC did not start")


def shutdown():
    lab.stop_nodes()
    lab.PROCS.clear()
    lab.OUTPUTS.clear()


def wait_for(condition, explanation, max_seconds=150):
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        for p, label in lab.PROCS:
            need(p.poll() is None, f"{label}: daemon exited unexpectedly")
        if condition():
            return
        time.sleep(2)
    raise RuntimeError(explanation)


def peers_live():
    info_a = lab.rpc(PORTS_A[1], "get_info")
    info_b = lab.rpc(PORTS_B[1], "get_info")
    return (int(info_a.get("outgoing_connections_count", 0)) +
            int(info_a.get("incoming_connections_count", 0)) > 0 and
            int(info_b.get("outgoing_connections_count", 0)) +
            int(info_b.get("incoming_connections_count", 0)) > 0)


def both_at(tip):
    return (lab.current_tip(PORTS_A[1]) == tip and
            lab.current_tip(PORTS_B[1]) == tip)


def main():
    daemon = lab.guard()
    source = (ROOT_SOURCE / "src/cryptonote_core/feelcoin_treasury.h").read_text()
    m = re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"', source)
    need(m is not None, "Public test mining address unavailable")
    address = m.group(1)
    root = pathlib.Path(tempfile.mkdtemp(prefix="feelcoin-v17-p2p-"))
    print(f"Stage 7 isolated log directory: {root}", flush=True)
    try:
        lab.say("Test-only P2P: connect two fakechain nodes over loopback")
        start(daemon, root, "node_a", PORTS_A, connected=True, copy_seed=True)
        start(daemon, root, "node_b", PORTS_B, connected=True, copy_seed=True)
        before = lab.current_tip(PORTS_A[1])
        need(before == lab.current_tip(PORTS_B[1]),
             "Initial synthetic histories differ")
        need(int(lab.header(PORTS_A[1], 120)["major_version"]) == 17,
             "Test fork does not activate v17 at block 120")
        wait_for(peers_live, "Loopback P2P handshake was not established", 120)
        print("PASS: both nodes established real loopback P2P connections",
              flush=True)

        lab.say("Mine v17 blocks and verify automatic network propagation")
        lab.mine(PORTS_A[1], 2, address, 4123)
        a_tip = lab.current_tip(PORTS_A[1])
        need(a_tip[0] == before[0] + 2, "Node A failed to mine 2 blocks")
        wait_for(lambda: lab.current_tip(PORTS_B[1]) == a_tip,
                 "Node B failed to sync mined A blocks over P2P")
        print(f"PASS: A -> B new v17 block propagation to height {a_tip[0]}",
              flush=True)
        lab.mine(PORTS_B[1], 1, address, 9123)
        b_tip = lab.current_tip(PORTS_B[1])
        wait_for(lambda: lab.current_tip(PORTS_A[1]) == b_tip,
                 "Node A failed to sync B-mined v17 block over P2P")
        print(f"PASS: B -> A new v17 block propagation to height {b_tip[0]}",
              flush=True)

        lab.say("Partition both nodes and independently mine competing v17 tips")
        shutdown()
        start(daemon, root, "node_a", PORTS_A, connected=False)
        start(daemon, root, "node_b", PORTS_B, connected=False)
        need(both_at(b_tip), "Restart changed the shared chain")
        lab.mine(PORTS_A[1], 1, address, 10003)
        lab.mine(PORTS_B[1], 3, address, 18003)
        short_tip = lab.current_tip(PORTS_A[1])
        heavy_tip = lab.current_tip(PORTS_B[1])
        need(short_tip[1] != heavy_tip[1] and
             heavy_tip[0] > short_tip[0],
             "Partition did not create competing tips")
        work_a = int(lab.header(PORTS_A[1], short_tip[0])["cumulative_difficulty"])
        work_b = int(lab.header(PORTS_B[1], heavy_tip[0])["cumulative_difficulty"])
        need(work_b > work_a, "Fork B is not stronger by cumulative work")
        print("PASS: disconnected nodes mined two distinct v17 branches",
              flush=True)
        shutdown()

        lab.say("Reconnect P2P: verify heavier v17 fork wins after partition")
        start(daemon, root, "node_a", PORTS_A, connected=True)
        start(daemon, root, "node_b", PORTS_B, connected=True)
        wait_for(peers_live, "P2P peers did not reconnect after partition")
        wait_for(lambda: both_at(heavy_tip),
                 "Post-partition P2P sync/reorg did not converge on stronger branch",
                 210)
        final_work_a = int(lab.header(PORTS_A[1], heavy_tip[0])
                           ["cumulative_difficulty"])
        need(final_work_a == work_b, "Converged cumulative work differs")
        print(f"PASS: isolated v17 partition rejoined; both peers agree at "
              f"height {heavy_tip[0]}", flush=True)
        print("PASS: P2P propagation, competing forks, cumulative-work reorg",
              flush=True)
        print("LIMIT: only two local fakechain peers with fixed difficulty 1; "
              "not a mixed-version mainnet fork or public network stress test.",
              flush=True)
    finally:
        shutdown()
        print(f"Artifacts: {root}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"STAGE 7 FAILED: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
