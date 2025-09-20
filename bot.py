import os
import random
import time
from solcx import compile_standard, install_solc
from web3 import Web3
from eth_account import Account

# ==============================
# Konfigurasi RPC & ChainID
# ==============================
RPCS = {
    "Base Mainnet": {
        "rpc": "https://developer-access-mainnet.base.org",
        "chainId": 8453
    },
    "Base Sepolia": {
        "rpc": "https://sepolia.base.org",
        "chainId": 84532
    },
    "MegaETH": {
        "rpc": "https://carrot.megaeth.com/rpc",
        "chainId": 6342
    },
    "Pharos": {
        "rpc": "https://testnet.dplabs-internal.com",
        "chainId": 688688
    },
    "Monad": {
        "rpc": "https://testnet-rpc.monad.xyz",
        "chainId": 10143
    },
    "Giwa": {
        "rpc": "https://sepolia-rpc.giwa.io",
        "chainId": 91342
    }
}

# ==============================
# Smart Contract (Counter)
# ==============================
CONTRACT_SOURCE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Counter {
    uint256 public count;

    function increment() public {
        count += 1;
    }
}
"""

# ==============================
# Utility
# ==============================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nTekan ENTER untuk lanjut...")

# ==============================
# Compile Solidity
# ==============================
def compile_counter():
    install_solc("0.8.20")
    compiled = compile_standard({
        "language": "Solidity",
        "sources": {"Counter.sol": {"content": CONTRACT_SOURCE}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}
        },
    }, solc_version="0.8.20")

    abi = compiled["contracts"]["Counter.sol"]["Counter"]["abi"]
    bytecode = compiled["contracts"]["Counter.sol"]["Counter"]["evm"]["bytecode"]["object"]
    return abi, bytecode

# ==============================
# Deploy Contract
# ==============================
def deploy_contract(w3, chainId, acct, abi, bytecode, nonce=None):
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    construct_txn = contract.constructor().build_transaction({
        "from": acct.address,
        "nonce": nonce if nonce is not None else w3.eth.get_transaction_count(acct.address),
        "gas": 2_000_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": chainId,
    })
    signed = acct.sign_transaction(construct_txn)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex(), receipt

# ==============================
# Menu: Batch Deploy
# ==============================
def menu_auto_batch():
    clear_screen()
    print("=== AUTO BATCH DEPLOY ===\n")

    n = int(input("Mau deploy berapa kontrak? : ").strip())

    print("\nPilih network:")
    for i, k in enumerate(RPCS.keys(), start=1):
        print(f" [{i}] {k}")
    net_keys = list(RPCS.keys())
    choice = int(input(f"Pilih (1-{len(net_keys)}): ").strip())
    net = net_keys[choice - 1]

    pk = input("Masukkan Private Key (0x...): ").strip()
    if not pk:
        print("[!] Private key wajib")
        pause()
        return
    acct = Account.from_key(pk)

    # Pilihan delay
    print("\nPilih tipe delay:")
    print(" [1] Random (min–max)")
    print(" [2] Fixed (detik tetap)")
    delay_choice = input("Pilih (1/2): ").strip()

    if delay_choice == "1":
        delay_min = float(input("Masukkan delay minimal (detik): ").strip())
        delay_max = float(input("Masukkan delay maksimal (detik): ").strip())
        delay_mode = "random"
    else:
        delay_fix = float(input("Masukkan delay tetap (detik): ").strip())
        delay_mode = "fixed"

    abi, bytecode = compile_counter()
    w3 = Web3(Web3.HTTPProvider(RPCS[net]["rpc"]))
    chainId = RPCS[net]["chainId"]

    nonce = w3.eth.get_transaction_count(acct.address)
    print(f"[i] Sender: {acct.address}, starting nonce {nonce}")

    for i in range(n):
        print(f"\n--- Deploy {i+1}/{n} ---")
        try:
            txh, rc = deploy_contract(w3, chainId, acct, abi, bytecode, nonce=nonce)
            print(f"[✓] Tx: {txh}")
            print(f"[✓] Contract: {rc['contractAddress']} (block {rc['blockNumber']}, status={rc['status']})")
            nonce += 1
        except Exception as e:
            print(f"[x] Gagal deploy: {e}")

        # Delay sesuai mode
        if delay_mode == "random":
            d = random.uniform(delay_min, delay_max)
        else:
            d = delay_fix
        print(f"[i] Delay {d:.1f}s...")
        time.sleep(d)

    pause()

# ==============================
# Main Menu
# ==============================
def main():
    while True:
        clear_screen()
        print("=== BOT DEPLOY CONTRACT ===\n")
        print("1. Auto Batch Deploy")
        print("0. Exit")
        ch = input("\nPilih menu: ").strip()
        if ch == "1":
            menu_auto_batch()
        elif ch == "0":
            break
        else:
            print("Pilihan tidak valid")
            pause()

if __name__ == "__main__":
    main()
