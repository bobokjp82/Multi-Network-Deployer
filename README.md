🚀 Multi-Network Smart Contract Deployer

Script Python ini memungkinkan kamu untuk deploy smart contract sederhana (Counter.sol) ke berbagai jaringan EVM-compatible dengan mudah.
Mendukung Base Mainnet, Base Sepolia, MegaETH, Pharos, Monad, dan Giwa Testnet.

Fitur utama:

🔧 Otomatis generate file Counter.sol jika belum ada

🛠️ Kompilasi Solidity (via solcx) dengan versi 0.8.24

🌐 Support banyak network (Base, MegaETH, Pharos, Monad, Giwa)

🔑 Input private key langsung di script

📦 Deploy 1x atau auto-batch deploy (deploy banyak kontrak sekaligus)

⏱️ Input delay waktu antar deploy (random antara min–max detik sesuai setting)

✅ Output detail transaksi: TX hash, contract address, block number, status


📦 Cara Install

Clone repo / download script
git clone https://github.com/bobokjp82/Multi-Network-Deployer.git


Buat virtual environment (opsional tapi disarankan)
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows


Install dependency
pip install web3 eth-account py-solc-x


Jalankan script
python bot.py
