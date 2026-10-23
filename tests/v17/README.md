# Feelcoin v17 isolated VPS test (NOT mainnet)

This is a **test-only branch** forked from `feature/v17-consensus-audit`. It changes **only the regtest/fakechain hardfork schedule** to activate v17 at **height 120**. Mainnet, testnet, stagenet, Node1, Node2 and production pools remain unchanged.

**Run on a dedicated spare Ubuntu VPS. Never run on Node1 or Node2.** The guarded script refuses known live daemon/services, mainnet ports and any accidentally configured mainnet v17 activation. It binds P2P/RPC/ZMQ to 127.0.0.1, uses `--regtest --offline`, creates a unique database under `/tmp`, and shuts down its daemon when the test ends. It does not enable or restart production services.

## One command after SSH into the spare VPS

```bash
git clone --depth 1 --branch test/v17-isolated-regtest --recurse-submodules https://github.com/feelcoin-org/feelcoin.git "$HOME/feelcoin-v17-regtest" && bash "$HOME/feelcoin-v17-regtest/tests/v17/isolated_vps_smoke.sh"
```

The script installs build dependencies, compiles the daemon and C++ unit tests, runs LWMA arithmetic and timestamp tests, starts an offline fakechain, and generates blocks 1–121 while checking v16 at height 119 and v17 at height 120.

### Important testing limits

- **This is only a smoke test**. `--fixed-difficulty 1` deliberately bypasses real LWMA retargeting to make block generation quick. The separate unit tests exercise the LWMA formula, but **live, variable-difficulty mining is still untested**.
- No validation yet for mainnet historical replay, two-node networking/reorganizations, miner/pool software compatibility, block time manipulation, or Windows binaries. Those are required release gates.
- The test rewards are **fakechain coins** paid to a public address from the project's source. No real miner keys, mainnet funds, or wallet files are used.
- C++ build or runtime tests can fail; such failures are useful diagnostic results and must be resolved before a production release.
- The fork activation block **18,400** discussed for production is only a proposal and is **not set by this script**.
- Do not merge the test branch into `main` or publish its regtest-only binaries as public v17 mainnet upgrades.

### What to share for debugging

Send the final script output. For any daemon problem, share the latest text from `/tmp/feelcoin-v17-regtest.*/daemon.stdout` and `feelcoind.log` **from this test VPS only**. Do not share private wallet material.
