#!/usr/bin/env python3
"""Repackage Tauri Ubuntu QA DEB with real native Core shared-library dependencies."""
import pathlib
import re
import subprocess
import sys
import tempfile

def run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout

def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: linux_deb_deps.py input.deb output.deb feelcoind feelcoin-wallet-rpc")
    src, dst = (pathlib.Path(x).resolve() for x in sys.argv[1:3])
    binaries = [pathlib.Path(x).resolve() for x in sys.argv[3:]]
    if not src.is_file() or any(not x.is_file() for x in binaries):
        raise SystemExit("ERROR: missing source DEB or ELF binary")
    with tempfile.TemporaryDirectory(prefix="feelcoin-qa-package-") as td:
        root = pathlib.Path(td)
        (root / "debian").mkdir()
        (root / "debian/control").write_text(
            "Source: feelcoin-desktop-qa\nSection: utils\nPriority: optional\n"
            "Maintainer: Feelcoin community <support@feelcoin.org>\nStandards-Version: 4.6.0\n\n"
            "Package: feelcoin-desktop-qa\nArchitecture: any\nDescription: QA dependency scan\n"
        )
        output = run(["dpkg-shlibdeps", "-O"] + ["-e" + str(x) for x in binaries], cwd=root)
        match = re.search(r"(?m)^shlibs:Depends=(.+)$", output)
        if not match:
            raise SystemExit("ERROR: dpkg-shlibdeps did not identify native Core dependencies")
        deps = match.group(1).strip()
        print("Core dependencies:", deps)
        unpacked = root / "package"
        run(["dpkg-deb", "-R", str(src), str(unpacked)])
        control = unpacked / "DEBIAN/control"
        text = control.read_text()
        pattern = re.compile(r"(?m)^Depends:[^\n]*(?:\n[ \t][^\n]*)*")
        m = pattern.search(text)
        if m:
            existing = m.group().split(":", 1)[1].replace("\n", " ").strip()
            merged = "Depends: " + existing + (", " if existing else "") + deps
            text = text[:m.start()] + merged + text[m.end():]
        else:
            text = text.rstrip("\n") + "\nDepends: " + deps + "\n"
        control.write_text(text)
        dst.parent.mkdir(parents=True, exist_ok=True)
        run(["dpkg-deb", "-b", str(unpacked), str(dst)])
        actual = run(["dpkg-deb", "--field", str(dst), "Depends"]).strip()
        print("Packaged dependencies:", actual)
        if "libboost" not in actual and "libicu" not in actual:
            raise SystemExit("ERROR: no native Boost or ICU runtime dependencies declared")
        print("PASS: distro-matched Linux DEB metadata")

if __name__ == "__main__":
    main()
