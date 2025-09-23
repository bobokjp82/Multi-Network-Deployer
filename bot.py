#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, pathlib, random, inspect
from web3 import Web3
from eth_account import Account
import solcx

# --- Patch untuk Python 3.12 (parsimonious butuh getargspec) ---
if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec

SOLC_VERSION = "0.8.24"

# Daftar RPC & ChainID
RPCS = {
    "base": ("https://base-rpc.publicnode.com", 8453),
    "base-sepolia": ("https://sepolia.base.org", 84532),
    "megaeth-testnet": ("https://carrot.megaeth.com/rpc", 6342),
    "pharos-testnet": ("https://testnet.dplabs-internal.com", 688688),
    "monad-testnet": ("https://testnet-rpc.monad.xyz", 10143),
    "giwa-testnet": ("https://sepolia-rpc.giwa.io", 91342),
}

# Kontrak default Counter
DEFAULT_COUNTER_SRC = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
contract Counter {
    uint256 public n;
    function inc() external { unchecked { n += 1; } }
}
"""

BANNER = r"""
=================================
 Multi Deployer by: Madeng Kasep
=================================
"""

# ---------- Helpers ----------
def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def pause():
    input("\nTekan ENTER untuk kembali ke menu...")

def ensure_solc():
    if str(SOLC_VERSION) not in [str(v) for v in solcx.get_installed_solc_versions()]:
        print(f"[i] Installing solc {SOLC_VERSION} ...")
        solcx.install_solc(SOLC_VERSION)
    solcx.set_solc_version(SOLC_VERSION)

def create_counter_file():
    p = pathlib.Path("Counter.sol")
    if not p.exists():
        p.write_text(DEFAULT_COUNTER_SRC, encoding="utf-8")
        print("[✓] Counter.sol dibuat")
    else:
        print("[!] Counter.sol sudah ada")

def compile_counter():
    ensure_solc()
    src = pathlib.Path("Counter.sol").read_text()
    comp = solcx.compile_source(src, output_values=["abi","bin"], solc_version=SOLC_VERSION)
    for fq, art in comp.items():
        if fq.endswith(":Counter"):
            return art["abi"], art["bin"]
    raise RuntimeError("Counter contract not found")

def connect(network_key: str):
    rpc, cid = RPCS[network_key]
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        raise RuntimeError(f"Gagal konek RPC {rpc}")
    return w3, cid

def eip1559_fees(w3):
    try: base = w3.eth.gas_price
    except: base = 1_000_000_000
    try:
        prio = w3.eth.max_priority_fee
        if prio is None: prio = int(1.5e9)
    except: prio = int(1.5e9)
    max_fee = int(base * 2 + prio)
    return max_fee, prio

def deploy_contract(w3, cid, acct, abi, bytecode, nonce=None):
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    max_fee, prio = eip1559_fees(w3)
    if nonce is None: nonce = w3.eth.get_transaction_count(acct.address)
    try:
        est = contract.constructor().estimate_gas({"from": acct.address})
    except: est = 1800000
    tx = contract.constructor().build_transaction({
        "from": acct.address,
        "chainId": cid,
        "nonce": nonce,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": prio,
        "gas": int(est*1.1),
    })
    signed = acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(signed.rawTransaction)
    rc = w3.eth.wait_for_transaction_receipt(txh)
    return txh.hex(), rc

# ---------- Menus ----------
def menu_deploy_network():
    clear_screen()
    print("\nPilih network:")
    for i, k in enumerate(RPCS.keys(), start=1):
        print(f" [{i}] {k}")
    net_keys = list(RPCS.keys())
    choice = int(input(f"Pilih (1-{len(net_keys)}): ").strip())
    net = net_keys[choice-1]

    pk = input("Masukkan Private Key (0x...): ").strip()
    if not pk:
        print("[!] Private key wajib"); pause(); return
    acct = Account.from_key(pk)

    jumlah = int(input("Mau deploy berapa kali?: ").strip())
    delay = int(input("Delay antar deploy (detik): ").strip())

    abi, bin_ = compile_counter()
    w3, cid = connect(net)

    nonce = w3.eth.get_transaction_count(acct.address)
    print(f"[i] Sender: {acct.address}, starting nonce {nonce}")

    for i in range(jumlah):
        print(f"\n--- Deploy {i+1}/{jumlah} ke {net} ---")
        try:
            txh, rc = deploy_contract(w3, cid, acct, abi, bin_, nonce=nonce)
            print(f"[✓] Tx: {txh}")
            print(f"[✓] Contract: {rc['contractAddress']} (block {rc['blockNumber']}, status={rc['status']})")
            nonce += 1
        except Exception as e:
            print(f"[x] Gagal deploy: {e}")
        if i < jumlah-1:
            print(f"[i] Delay {delay}s..."); time.sleep(delay)
    pause()

def menu_auto_batch():
    clear_screen()
    n = int(input("Mau deploy berapa kontrak?: ").strip())

    print("\nPilih network:")
    for i, k in enumerate(RPCS.keys(), start=1):
        print(f" [{i}] {k}")
    net_keys = list(RPCS.keys())
    choice = int(input(f"Pilih (1-{len(net_keys)}): ").strip())
    net = net_keys[choice-1]

    pk = input("Masukkan Private Key (0x...): ").strip()
    if not pk:
        print("[!] Private key wajib"); pause(); return
    acct = Account.from_key(pk)

    abi, bin_ = compile_counter()
    w3, cid = connect(net)

    nonce = w3.eth.get_transaction_count(acct.address)
    for i in range(n):
        print(f"\n--- Deploy {i+1}/{n} ---")
        try:
            txh, rc = deploy_contract(w3, cid, acct, abi, bin_, nonce=nonce)
            print(f"[✓] Tx: {txh}")
            print(f"[✓] Contract: {rc['contractAddress']}")
            nonce += 1
        except Exception as e:
            print(f"[x] Gagal deploy: {e}")
        time.sleep(random.uniform(3,5))
    pause()

def menu_multi_wallet():
    clear_screen()
    print("[i] Membaca wallets.txt ...")
    if not pathlib.Path("wallets.txt").exists():
        print("[!] Buat file wallets.txt dulu, isi 1 private key per baris")
        pause(); return
    wallets = [l.strip() for l in open("wallets.txt") if l.strip()]

    print("\nPilih network:")
    for i, k in enumerate(RPCS.keys(), start=1):
        print(f" [{i}] {k}")
    net_keys = list(RPCS.keys())
    choice = int(input(f"Pilih (1-{len(net_keys)}): ").strip())
    net = net_keys[choice-1]

    jumlah = int(input("Mau deploy berapa kali per wallet?: ").strip())
    delay = int(input("Delay antar deploy (detik): ").strip())

    abi, bin_ = compile_counter()
    w3, cid = connect(net)

    for pk in wallets:
        acct = Account.from_key(pk)
        nonce = w3.eth.get_transaction_count(acct.address)
        print(f"\n=== Wallet {acct.address} ===")
        for i in range(jumlah):
            print(f"\n--- Deploy {i+1}/{jumlah} ---")
            try:
                txh, rc = deploy_contract(w3, cid, acct, abi, bin_, nonce=nonce)
                print(f"[✓] Tx: {txh}")
                print(f"[✓] Contract: {rc['contractAddress']}")
                nonce += 1
            except Exception as e:
                print(f"[x] Gagal deploy: {e}")
            if i < jumlah-1:
                print(f"[i] Delay {delay}s..."); time.sleep(delay)
    pause()

def menu_multi_chain():
    clear_screen()
    pk = input("Masukkan Private Key (0x...): ").strip()
    if not pk:
        print("[!] Private key wajib"); pause(); return
    acct = Account.from_key(pk)

    jumlah = int(input("Mau deploy berapa kali per chain?: ").strip())
    delay = int(input("Delay antar deploy (detik): ").strip())

    abi, bin_ = compile_counter()

    for net, (rpc, cid) in RPCS.items():
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            print(f"[x] Gagal konek ke {net}")
            continue
        nonce = w3.eth.get_transaction_count(acct.address)
        print(f"\n=== Deploy ke {net} ===")
        for i in range(jumlah):
            print(f"\n--- Deploy {i+1}/{jumlah} ---")
            try:
                txh, rc = deploy_contract(w3, cid, acct, abi, bin_, nonce=nonce)
                print(f"[✓] Tx: {txh}")
                print(f"[✓] Contract: {rc['contractAddress']}")
                nonce += 1
            except Exception as e:
                print(f"[x] Gagal deploy: {e}")
            if i < jumlah-1:
                print(f"[i] Delay {delay}s..."); time.sleep(delay)

    verify = input("\nMau verify kontrak di explorer? (y/n): ").strip().lower()
    if verify == "y":
        print("[i] Fitur verify kontrak belum diimplementasi, tambahkan manual jika perlu.")
    pause()

def main_menu():
    ensure_solc()
    while True:
        clear_screen()
        print(BANNER)
        print("""
 Pilih menu:
 [1] Buat template Counter.sol
 [2] Deploy ke Network Tertentu
 [3] Auto batch deploy (1 wallet, banyak kontrak)
 [4] Multi-wallet deploy
 [5] Multi-chain deploy (+ optional verify)
 [q] Keluar
""")
        c = input(" Pilih menu: ").strip().lower()
        if c == "1": clear_screen(); create_counter_file(); pause()
        elif c == "2": menu_deploy_network()
        elif c == "3": menu_auto_batch()
        elif c == "4": menu_multi_wallet()
        elif c == "5": menu_multi_chain()
        elif c == "q": clear_screen(); print("Bye!"); break
        else:
            print("[!] Menu tidak valid"); time.sleep(1)

if __name__=="__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        clear_screen(); print("\n^C exit")
