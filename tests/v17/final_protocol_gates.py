#!/usr/bin/env python3
"""Feelcoin v17 isolated release-gate batch: invalid blocks, fork replay, restart.

Run ONLY as feelv17 on the named spare VPS. Everything stays on loopback in
temporary fakechain databases. No production nodes, wallets, or mainnet data.
"""
import hashlib
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import time

import next_stage_vps as lab

SOURCE = pathlib.Path(__file__).resolve().parents[2]


def expect(condition, message):
    if not condition:
        raise RuntimeError(message)


def varint_read(data, off):
    value = 0
    shift = 0
    while True:
        expect(off < len(data) and shift < 70, "Invalid block header varint")
        n = data[off]
        off += 1
        value |= (n & 127) << shift
        if not n & 128:
            return value, off
        shift += 7


def varint_write(n):
    expect(0 <= n <= (1 << 64) - 1, "Varint value outside uint64")
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def mutate_header(blob, field, value):
    raw = bytes.fromhex(blob)
    positions = []
    off = 0
    for _ in range(3):
        v, end = varint_read(raw, off)
        positions.append((off, end, v))
        off = end
    expect(positions[0][2] == 17, "Expected candidate v17 block header")
    expect(positions[1][2] >= 16, "Unexpected block minor version")
    expect(len(raw) > off + 36, "Unexpectedly short block blob")
    index = {"version": 0, "timestamp": 2}[field]
    begin, end, _ = positions[index]
    return (raw[:begin] + varint_write(value) + raw[end:]).hex()


def guarded_submit(port, blob, expected_tip, description, marker=None, logpath=None):
    # Only a real RPC-level block rejection qualifies. Network/timeouts are
    # harness failures, never evidence of correctly enforced consensus.
    try:
        lab.rpc(port, "submit_block", [blob], timeout=45)
    except RuntimeError as exc:
        expect(str(exc).startswith(f"RPC submit_block at {port}: "),
               description + f": unexpected runtime error: {exc}")
    else:
        raise RuntimeError(description + " was incorrectly ACCEPTED!")
    expect(lab.current_tip(port) == expected_tip,
           description + " changed the canonical chain")
    if marker:
        # Diagnostic logger may flush just after the JSON-RPC response.
        found = False
        for _ in range(20):
            if logpath and marker in logpath.read_text(errors="replace"):
                found = True
                break
            time.sleep(0.1)
        expect(found,
               description + ": specific consensus rejection reason not in diagnostic log")
    print(f"PASS: {description} rejected; chain unchanged", flush=True)


def check_historical_versions(port, top):
    # These are isolated synthetic blocks, not production blockchain history.
    expect(top >= 121, f"Seed tip unexpectedly short: {top}")
    first = lab.header(port, 1)
    previous_work = int(first["cumulative_difficulty"])
    for height in range(1, 122):
        hdr = lab.header(port, height)
        want = 16 if height < 120 else 17
        expect(int(hdr["major_version"]) == want,
               f"Fork replay height {height}: expected v{want}, got {hdr['major_version']}")
        cum = int(hdr["cumulative_difficulty"])
        expect(cum > 0 and (height == 1 or cum > previous_work),
               f"Non-increasing cumulative work at {height}")
        previous_work = cum
    print("PASS: replayed 121 synthetic headers; v16 <120, v17 >=120", flush=True)
    return lab.header(port, 119)["hash"], lab.header(port, 120)["hash"]


def restart_existing(daemon, root, ports):
    p2p, rpc, zmq = ports
    output = (root / "restart.stdout").open("w")
    lab.OUTPUTS.append(output)
    args = [
        str(daemon), "--regtest", "--offline", "--keep-fakechain",
        "--fixed-difficulty", "1", "--non-interactive",
        "--data-dir", str(root / "node_a/data"),
        "--log-file", str(root / "restart.log"),
        "--p2p-bind-ip", "127.0.0.1", "--p2p-bind-port", str(p2p),
        "--rpc-bind-ip", "127.0.0.1", "--rpc-bind-port", str(rpc),
        "--zmq-rpc-bind-ip", "127.0.0.1", "--zmq-rpc-bind-port", str(zmq),
        "--rpc-ssl", "disabled", "--no-igd", "--disable-dns-checkpoints",
        "--check-updates", "disabled",
    ]
    proc = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT,
                            start_new_session=True)
    lab.PROCS.append((proc, "restart"))
    for _ in range(60):
        expect(proc.poll() is None, f"Restart daemon failed: {proc.returncode}")
        try:
            info = lab.rpc(rpc, "get_info", timeout=5)
            expect(info.get("nettype") == "fakechain", "Not an offline fakechain")
            return
        except (OSError, ValueError):
            time.sleep(1)
    raise RuntimeError("Daemon RPC not ready after restart")


def main():
    daemon = lab.guard()
    source = (SOURCE / "src/cryptonote_core/feelcoin_treasury.h").read_text()
    match = re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"', source)
    expect(match is not None, "Synthetic payout address missing")
    address = match.group(1)
    root = pathlib.Path(tempfile.mkdtemp(prefix="feelcoin-v17-gate-"))
    print("Isolated logs:", root, flush=True)
    port_a, port_b = lab.TEST_PORTS[0][1], lab.TEST_PORTS[1][1]
    try:
        lab.say("Review v16/v17 historical boundary from synthetic chain")
        ha = lab.start_node(
            daemon, root, "node_a", lab.TEST_PORTS[0], fixed=True,
            log_level="*:WARNING,verify:DEBUG,cn:INFO,logging:INFO")
        expect(ha >= 122, f"Expected synthetic chain of at least 122 blocks, got {ha}")
        initial_tip = lab.current_tip(port_a)
        historical = check_historical_versions(port_a, initial_tip[0])
        logpath = root / "node_a.log"
        categories = logpath.read_text(errors="replace")
        expect("verify:DEBUG" in categories,
               "Diagnostic verify logging is not enabled; cannot prove rejection reason")

        lab.say("Adversarial main-chain block/header validation")
        t = lab.rpc(port_a, "get_block_template",
                    {"wallet_address": address, "reserve_size": 1})
        blob = t["blocktemplate_blob"]
        head_major, _ = varint_read(bytes.fromhex(blob), 0)
        expect(head_major == 17, "New template did not activate v17")
        far_future = int(time.time()) + 3600
        guarded_submit(port_a, mutate_header(blob, "timestamp", far_future),
                       initial_tip, "v17 +3600-second future timestamp",
                       "exceeds the permitted future tolerance for consensus version 17",
                       logpath)
        guarded_submit(port_a, mutate_header(blob, "timestamp", 1),
                       initial_tip, "v17 below-median past timestamp",
                       "less than median", logpath)
        guarded_submit(port_a, mutate_header(blob, "version", 16),
                       initial_tip, "obsolete v16 block at v17 height",
                       "has old version", logpath)
        guarded_submit(port_a, mutate_header(blob, "version", 18),
                       initial_tip, "unscheduled v18 block at v17 height")
        guarded_submit(port_a, "zzzz", initial_tip, "malformed block blob")
        print("PASS: v17 negative block tests completed", flush=True)

        lab.say("Adversarial alternative-chain timestamp validation")
        hb = lab.start_node(
            daemon, root, "node_b", lab.TEST_PORTS[1], fixed=True,
            log_level="*:WARNING,verify:DEBUG,cn:INFO,logging:INFO")
        expect(hb == ha, "Fakechain seeds differ in height")
        expect(lab.current_tip(port_b) == lab.current_tip(port_a),
               "Fakechain seeds differ in hash")
        lab.mine(port_a, 2, address, 231)
        a_tip = lab.current_tip(port_a)
        lab.mine(port_b, 1, address, 1092)
        b_blob = lab.rpc(port_b, "get_block", {"height": ha})["blob"]
        expect(lab.header(port_a, ha)["hash"] !=
               lab.header(port_b, ha)["hash"], "Branches did not diverge")
        guarded_submit(port_a, mutate_header(b_blob, "timestamp",
                                            int(time.time()) + 3600),
                       a_tip, "v17 alternative-chain future timestamp",
                       "Feelcoin v17 alternative block timestamp exceeds future tolerance",
                       logpath)
        # The original competing block remains valid and may be stored as an alt.
        lab.rpc(port_a, "submit_block", [b_blob])
        expect(lab.current_tip(port_a) == a_tip,
               "Shorter alternative chain unexpectedly replaced main tip")
        lab.mine(port_b, 3, address, 1093)
        for h in range(ha + 1, lab.current_tip(port_b)[0] + 1):
            valid_blob = lab.rpc(port_b, "get_block", {"height": h})["blob"]
            lab.rpc(port_a, "submit_block", [valid_blob])
        expect(lab.current_tip(port_a) == lab.current_tip(port_b),
               "Higher-work valid branch failed to become canonical")
        new_tip = lab.current_tip(port_a)
        print("PASS: invalid alternative rejected, valid higher-work branch accepted",
              flush=True)

        lab.say("Restart same isolated blockchain and verify persistence")
        lab.stop_nodes()
        lab.PROCS.clear()
        lab.OUTPUTS.clear()
        restart_existing(daemon, root, lab.TEST_PORTS[0])
        expect(lab.current_tip(port_a) == new_tip,
               "Canonical chain changed after daemon restart")
        expect((lab.header(port_a, 119)["hash"],
                lab.header(port_a, 120)["hash"]) == historical,
               "Historical block hashes changed after restart")
        check_historical_versions(port_a, new_tip[0])
        print("PASS: replayed chain, v17 fork boundary and reorganized tip survive restart",
              flush=True)

        lab.say("Binary/protocol release guard")
        digest = hashlib.sha256(daemon.read_bytes()).hexdigest()
        mainnet = (SOURCE / "src/hardforks/hardforks.cpp").read_text()
        mainnet = mainnet.split("mainnet_hard_forks", 1)[-1].split("};", 1)[0]
        expect(not re.search(r"\{\s*17\s*,", mainnet),
               "Mainnet v17 activation unexpectedly present")
        expect(subprocess.check_output(["git", "-C", str(SOURCE),
                                        "status", "--porcelain", "--untracked-files=no"], text=True).strip() == "",
               "Dirty test checkout; stop before release")
        print("Linux daemon SHA256:", digest, flush=True)
        print("PASS: isolated branch, clean source, no mainnet v17 activation",
              flush=True)
        print("PASS: isolated Stage 5 protocol gates", flush=True)
        print("LIMIT: synthetic history only; live mainnet replay, network-partition",
              "resilience and Windows packaging are separate release gates.",
              flush=True)
    except Exception as exc:
        print("FAIL:", exc, file=sys.stderr, flush=True)
        for path in root.glob("*.log"):
            print(f"--- {path.name} tail ---", file=sys.stderr)
            print("\n".join(path.read_text(errors="replace").splitlines()[-18:]),
                  file=sys.stderr)
        raise
    finally:
        lab.stop_nodes()
        print("Log directory:", root, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
