#!/usr/bin/env bash
# ISOLATED VPS ONLY. No production Feelcoin network, wallets, or nodes.
set -Eeuo pipefail
umask 077
fail() { echo "STOP: $*" >&2; exit 1; }
say() { echo; echo "=== $* ==="; }

[[ "$EUID" -ne 0 ]] || fail "Run as a regular user, not root."
[[ "$(uname -s)" == Linux ]] || fail "Linux required."
command -v sudo >/dev/null || fail "sudo is required."
command -v systemctl >/dev/null || fail "Use a dedicated Ubuntu VPS with systemd."
command -v ss >/dev/null || fail "ss is missing."
command -v apt-get >/dev/null || fail "Ubuntu/Debian with apt is required."

HERE="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$(cd "$HERE/../.." && pwd)"
[[ "$(git -C "$SOURCE" branch --show-current)" == test/v17-isolated-regtest ]] ||
  fail "Not on isolated regtest branch."
grep -Fq 'std::make_pair(uint8_t(17), 120)' "$SOURCE/src/cryptonote_core/cryptonote_core.cpp" ||
  fail "Regtest activation definition missing."
if sed -n '/const hardfork_t mainnet_hard_forks/,/^};/p' "$SOURCE/src/hardforks/hardforks.cpp" |
   grep -Eq '\{[[:space:]]*17[[:space:]]*,'; then
  fail "A mainnet activation is present. Refusing."
fi

HOST="$(hostname -f 2>/dev/null || hostname)"
case "$HOST" in
  *node1.feelcoin.org*|*node2.feelcoin.org*) fail "Production Feelcoin host." ;;
esac
# A disabled, inactive feelcoin-miner.service is harmless. Refuse only
# active production-like daemon, pool or node services, and running daemons.
if pgrep -x feelcoind >/dev/null 2>&1 ||
   systemctl --no-pager --plain list-units --state=running --type=service 2>/dev/null |
      grep -Eiq 'feelcoin.*(daemon|node|pool).*service'; then
  fail "An active Feelcoin daemon, node or pool was detected. Use another VPS."
fi
if ss -ltn | grep -Eq ':(35780|35781|35782)[[:space:]]'; then
  fail "Production-like Feelcoin port detected."
fi

if [[ "${V17_SKIP_APT:-0}" == "1" ]]; then
  say "Build dependencies already installed by the VPS administrator"
else
  say "Install build dependencies on the dedicated lab VPS"
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential cmake git pkg-config python3 ca-certificates \
    libboost-all-dev libunbound-dev libssl-dev \
    libzmq3-dev libsodium-dev libhidapi-dev libusb-1.0-0-dev \
    libprotobuf-dev protobuf-compiler libreadline-dev libgtest-dev
fi

say "Build an isolated daemon and unit tests"
git -C "$SOURCE" submodule update --init --recursive
LAB="$(mktemp -d /tmp/feelcoin-v17-regtest.XXXXXXXX)"
echo "Lab directory: $LAB"
cmake -S "$SOURCE" -B "$LAB/build" \
  -D ARCH=default -D CMAKE_BUILD_TYPE=Release -D BUILD_TESTS=ON
cmake --build "$LAB/build" --target daemon unit_tests -j2
DAEMON="$LAB/build/bin/feelcoind"
TESTER="$LAB/build/bin/unit_tests"
[[ -x "$DAEMON" && -x "$TESTER" ]] || fail "Build outputs missing."

say "Run v17 difficulty and timestamp unit tests"
"$TESTER" --gtest_filter='difficulty.feelcoin_lwma_*:feelcoin_timestamp.*' --gtest_color=no

say "Start loopback-only offline fakechain"
for port in 45980 45981 45982; do
  if ss -ltn | grep -Eq ":$port[[:space:]]"; then fail "Test port in use: $port"; fi
done
mkdir -p "$LAB/data"
"$DAEMON" --regtest --offline --fixed-difficulty 1 --non-interactive \
  --data-dir "$LAB/data" --log-file "$LAB/feelcoind.log" \
  --p2p-bind-ip 127.0.0.1 --p2p-bind-port 45980 \
  --rpc-bind-ip 127.0.0.1 --rpc-bind-port 45981 \
  --zmq-rpc-bind-ip 127.0.0.1 --zmq-rpc-bind-port 45982 \
  --rpc-ssl disabled --no-igd --disable-dns-checkpoints \
  --check-updates disabled >"$LAB/daemon.stdout" 2>&1 &
PID=$!
cleanup() {
  if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" || true
    wait "$PID" || true
  fi
}
trap cleanup EXIT

say "Generate fakechain blocks and check v16 -> v17 at height 120"
export V17_SOURCE="$SOURCE"
python3 - <<'PY'
import json, os, pathlib, re, time, urllib.request
endpoint = "http://127.0.0.1:45981/json_rpc"

def rpc(method, params=None):
    data=json.dumps({"jsonrpc":"2.0","id":"lab","method":method,"params":params or {}}).encode()
    req=urllib.request.Request(endpoint,data,{"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        result=json.load(response)
    if result.get("error"):
        raise RuntimeError(str(result["error"]))
    result=result["result"]
    if result.get("status") not in (None,"OK"):
        raise RuntimeError(str(result))
    return result

for attempt in range(60):
    try:
        info=rpc("get_info")
        break
    except Exception:
        time.sleep(2)
else:
    raise RuntimeError("Regtest daemon RPC did not start.")
assert info.get("nettype") == "fakechain", "Not a fakechain; abort"
source=pathlib.Path(os.environ["V17_SOURCE"],"src/cryptonote_core/feelcoin_treasury.h").read_text()
match=re.search(r'static constexpr const char \*ADDRESS\s*=\s*"([^"]+)"',source)
if not match:
    raise RuntimeError("Public test payout address not found.")
addr=match.group(1)
print("Isolated network:",info["nettype"],flush=True)
print("Generating 119 fakechain blocks ...",flush=True)
rpc("generateblocks",{"amount_of_blocks":119,"wallet_address":addr,"starting_nonce":0})
pre=rpc("get_block_header_by_height",{"height":119})["block_header"]["major_version"]
assert pre==16, "Expected v16 at height 119, got "+str(pre)
print("Height 119 => v16 CONFIRMED",flush=True)
rpc("generateblocks",{"amount_of_blocks":2,"wallet_address":addr,"starting_nonce":0})
post=rpc("get_block_header_by_height",{"height":120})["block_header"]["major_version"]
assert post==17, "Expected v17 at height 120, got "+str(post)
print("Height 120 => v17 CONFIRMED",flush=True)
print("PASS: Isolated fork version boundary. NOTE: fixed difficulty bypasses LWMA live mining.",flush=True)
PY

say "Regtest smoke completed; stopping daemon; Node1 and Node2 untouched"
echo "Artifacts in $LAB"
