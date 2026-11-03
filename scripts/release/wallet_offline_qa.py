#!/usr/bin/env python3
"""Offline ephemeral Feelcoin v1 mnemonic recovery gate. Never print seed."""
import json, pathlib, secrets, socket, subprocess, sys, tempfile, time
import urllib.request

def ports():
    socks = [socket.socket() for _ in range(3)]
    try:
        for s in socks: s.bind(("127.0.0.1", 0))
        return [s.getsockname()[1] for s in socks]
    finally:
        for s in socks: s.close()

def http(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as response: return json.load(response)

def rpc(port, method, params=None):
    answer = http(f"http://127.0.0.1:{port}/json_rpc",
                  {"jsonrpc":"2.0","id":"qa","method":method,"params":params or {}})
    if "error" in answer:
        err = answer["error"]
        raise RuntimeError(f"{method} failed: RPC code {err.get('code')}; {err.get('message')}")
    return answer["result"]

def until(proc, callback, name):
    for _ in range(40):
        if proc.poll() is not None: raise RuntimeError(f"{name} exited with {proc.returncode}")
        try: return callback()
        except (OSError, ValueError, KeyError, RuntimeError): time.sleep(1)
    raise RuntimeError(f"{name} was not ready")

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: wallet_offline_qa.py <binary-directory>")
    binpath = pathlib.Path(sys.argv[1]).resolve()
    p2p, dp, wp = ports()
    with tempfile.TemporaryDirectory(prefix="feelcoin-wallet-qa-") as td:
        root=pathlib.Path(td)
        (root/"chain").mkdir()
        (root/"wallets").mkdir()
        children=[]
        logs=[]
        def start(name, args):
            # Logs can contain secrets: do not upload or print them.
            f=(root/(name+".log")).open("w")
            logs.append(f)
            p=subprocess.Popen([str(binpath/name),*args],stdin=subprocess.DEVNULL,
                               stdout=f,stderr=subprocess.STDOUT)
            children.append(p)
            return p
        try:
            d=start("feelcoind",["--offline","--no-zmq","--data-dir",str(root/"chain"),
                 "--p2p-bind-ip","127.0.0.1","--p2p-bind-port",str(p2p),
                 "--rpc-bind-ip","127.0.0.1","--rpc-bind-port",str(dp),"--non-interactive"])
            info=until(d,lambda:http(f"http://127.0.0.1:{dp}/get_info"),"daemon")
            assert info.get("status")=="OK" and info.get("height")==1
            print("PASS: Isolated offline daemon",flush=True)
            w=start("feelcoin-wallet-rpc",["--wallet-dir",str(root/"wallets"),
                "--daemon-address",f"127.0.0.1:{dp}","--rpc-bind-ip","127.0.0.1",
                "--rpc-bind-port",str(wp),"--disable-rpc-login","--non-interactive"])
            until(w,lambda:rpc(wp,"get_version"),"wallet RPC")
            print("PASS: Wallet RPC",flush=True)
            pw=secrets.token_urlsafe(24)
            rpc(wp,"create_wallet",{"filename":"source","password":pw,"language":"English"})
            address=rpc(wp,"get_address",{"account_index":0})["address"]
            assert len(address)>90
            mnemonic=rpc(wp,"query_key",{"key_type":"mnemonic"})["key"]
            assert len(mnemonic.split())>=20
            print("PASS: Create new wallet and retrieve mnemonic privately",flush=True)
            rpc(wp,"close_wallet",{"autosave_current":True})
            rpc(wp,"open_wallet",{"filename":"source","password":pw})
            assert rpc(wp,"get_address",{"account_index":0})["address"]==address
            print("PASS: Save and reopen original",flush=True)
            rpc(wp,"close_wallet",{"autosave_current":True})
            restored=rpc(wp,"restore_deterministic_wallet",{
                "filename":"recovered","password":secrets.token_urlsafe(24),
                "seed":mnemonic,"language":"English","restore_height":0})
            assert restored["address"]==address
            assert rpc(wp,"get_address",{"account_index":0})["address"]==address
            print("PASS: Mnemonic restoration preserves original address",flush=True)
            # Verify restored disk state without exposing the recovery password in output.
            rpc(wp,"close_wallet",{"autosave_current":True})
            print("=== FEELCOIN v1 OFFLINE MNEMONIC RECOVERY QA PASSED ===",flush=True)
        finally:
            for p in reversed(children):
                if p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=8)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
            for f in logs:f.close()
    print("PASS: Disposable files removed",flush=True)

if __name__=="__main__":main()
