# Feelcoin v17 — chosen target block 21,205

**Decision: October 24, 2026. Target approved by the developer as a release-planning choice, not a finished production deployment.**

From developer-observed block height **16,144**, the observed **119.5s/block** gives approximately **5,061 blocks per seven-day interval**, so target **21,205**. This estimated week of blocks **does not guarantee seven days of notice** after binaries become publicly available.

Release candidate pins Core **v1.0.0** and mainnet HF **v17** at block **21,205**, with threshold 0, while earlier blocks remain v16. Testnet/stagenet schedules remain v16. All consensus economics (2% treasury, reward, RandomX, 120s target) are unchanged.

**Release safeguards:** Do not release or deploy this hardfork candidate if the review, Wallet CLI/RPC DLL fix, Windows antivirus retest, Linux and Desktop v1.0 matching binaries, independent hardfork test, checksums, pool readiness, or public notice are incomplete. If block 21,205 arrives before sufficient community notice, choose a later height *with the developer* and rebuild before deploying, rather than force the early fork. Node1/Node2 must remain v16 until final approval.

The Windows Core candidate ZIP is produced from an exact allowlist of native Windows EXEs, recursively discovered MinGW runtime DLLs, README and checksum file. It includes no Linux binaries, source trees, .so, DEB, AppImage or shell scripts.