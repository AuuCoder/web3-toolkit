# Utils - Utility Scripts

English | [简体中文](./README.md)

A collection of commonly used Web3 development utility scripts.

## Tools List

### 1. generate_wallets.py - EVM Wallet Batch Generator

Batch generate EVM wallet addresses and private keys.

#### Features

- 🔐 Batch generate EVM wallets (supports all EVM-compatible chains)
- 💾 Auto-save private keys to JSON file (wallet.json format)
- 📋 Generate detailed information file (with address-privatekey mapping)
- 🎨 User-friendly command-line interface
- ✅ Safety checks and confirmation mechanism

#### Installation

```bash
cd utils
pip install -r requirements.txt
```

#### Usage

##### Interactive Mode

```bash
python generate_wallets.py
```

Follow the prompts to enter:

1. Number of wallets to generate (default 10)
2. Output file name (default wallet.json)

##### Use in Code

```python
from generate_wallets import generate_wallets

# Generate 50 wallets, save to my_wallets.json
wallets = generate_wallets(count=50, output_file="my_wallets.json")
```

#### Output Files

The script generates two files:

1. **wallet.json** - Array of private keys only (for use with other scripts)

```json
["0xabc123...", "0xdef456...", "0xghi789..."]
```

2. **wallet_detail.json** - Complete information (for viewing mappings)

```json
[
  {
    "index": 1,
    "address": "0x1234...",
    "private_key": "0xabc123..."
  },
  {
    "index": 2,
    "address": "0x5678...",
    "private_key": "0xdef456..."
  }
]
```

#### Example

```bash
$ python generate_wallets.py
======================================================================
  🌟 EVM Wallet Batch Generator 🌟
======================================================================

Enter number of wallets to generate (default 10): 5
Enter output file name (default wallet.json): my_wallets.json

🔐 Generating 5 EVM wallets...
======================================================================
[  1] Address: 0x1234************************************5678
      Private Key: 0xabcdef****************************************************7890
----------------------------------------------------------------------
[  2] Address: 0xabcd************************************abcd
      Private Key: 0x123456****************************************************abcd
----------------------------------------------------------------------
...

======================================================================
✅ Successfully generated 5 wallets!
💾 Private keys saved to: my_wallets.json

⚠️  Important Reminder:
   - Keep the private key file safe, do not leak it!
   - These are real wallet private keys that can be used on any EVM chain
   - Recommended to backup to a secure location
📋 Detailed information (address + private key) saved to: my_wallets_detail.json
```

#### Use Cases

- 🧪 Batch create test wallets
- 🌊 Use with faucet scripts to batch claim test tokens
- 🔄 Batch airdrop or distribution operations
- 📊 Stress testing and performance testing

#### Security Notes

⚠️ **Security Warning**:

- Generated private keys are real and usable, please keep them safe
- Do not upload files containing private keys to public places
- Recommended to use only on test networks
- Files are automatically added to `.gitignore`

#### Supported Chains

Supports all EVM-compatible blockchains, including but not limited to:

- Ethereum (ETH)
- Binance Smart Chain (BSC)
- Polygon (MATIC)
- Avalanche (AVAX)
- Arbitrum
- Optimism
- All other EVM-compatible chains

## License

MIT
