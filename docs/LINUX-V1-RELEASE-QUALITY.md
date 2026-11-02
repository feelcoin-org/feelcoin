# Feelcoin v1 Linux installation quality gate

QA ONLY. No production release, hardfork activation, wallet migration or live transfers.

**Root issue:** Core compiled on Ubuntu 22.04 loads Boost 1.74 and ICU 70;
Ubuntu 26.04 has newer ABI versions. An old bundled libcom_err.so.2 also
broke Linux Desktop packaging on Ubuntu 22.04 through GLIBC_2.38.

**Remediation in v1-linux-native-install-qa.yml:**
1. Compile the exact pinned Core and full Desktop GUI source on GitHub's
   Ubuntu 22.04, 24.04 and 26.04 runners independently.
2. Remove any legacy binary/library resources before adding native ELFs.
3. Package separate labeled DEB and AppImage QA artifacts per distro; inspect
   package contents for binaries and reject Windows files.
4. Compute actual Core dependencies using dpkg-shlibdeps, merge into the
   installer metadata. On a completely fresh matching runner, apt-install
   the DEB and verify both bundled ELF programs and their dynamic links.
5. Verify SHA256SUMS for all test artifacts. An AppImage built for one
   version is NOT a promise of compatibility with other Linux versions.

**Release approval still requires:** interactive GUI tests on the three
distros, disposable-wallet create/recover/sync/send flows, actual
AppImage execution (not only extraction), Windows antivirus/smoke checks,
Android original release signing-key verification, consensus/security
audit and adequate mainnet v17 operator notice. Do not use QA artifacts
with real funds. Native clean-install tests do not replace these gates.
