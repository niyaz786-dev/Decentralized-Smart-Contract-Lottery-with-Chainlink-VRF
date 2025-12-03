# Smart Contract Lottery

## Overview
This repository contains a **decentralized lottery** smart contract built with **Solidity** and **Brownie**. It leverages **Chainlink VRF v2.5** for provably fair random winner selection and **Chainlink Price Feeds** to dynamically calculate entry fees in USD.

### Features
- **Provably Fair:** Uses Chainlink VRF (Verifiable Random Function) to select winners.
- **Dynamic Pricing:** Entry fee is pegged to USD (e.g., $50) but paid in ETH, using Chainlink Price Feeds.
- **Automated:** Scripts to deploy, start, enter, and end the lottery.
- **Testnet Ready:** Configured for Sepolia testnet.

## Project Structure
```
smartcontract-lottery/
├─ contracts/
│   └─ Lottery.sol          # The main smart contract
├─ scripts/
│   ├─ deploy_lottery.py    # Deploys contract to network
│   ├─ finish_lottery.py    # Runs a full lottery cycle (Start -> Enter -> End)
│   ├─ check_status.py      # Checks current lottery state and winner
│   └─ helpful_scripts.py   # Utilities (account management, mocking)
├─ brownie-config.yaml      # Network and dependency configuration
├─ .env                     # Private keys (not committed)
└─ README.md                # Documentation
```

## Prerequisites
- **Python 3.11+**
- **Brownie** (`pip install eth-brownie`)
- **Infura/Alchemy** Project ID (for Sepolia)
- **Chainlink VRF Subscription** (funded with LINK)

## Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd smartcontract-lottery
   ```

2. **Install dependencies:**
   ```bash
   pip install eth-brownie
   brownie pm install smartcontractkit/chainlink-brownie-contracts@1.2.0
   brownie pm install OpenZeppelin/openzeppelin-contracts@4.8.0
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```dotenv
   PRIVATE_KEY=0xYOUR_PRIVATE_KEY
   WEB3_PROVIDER_URI=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
   ```

4. **Update Configuration:**
   In `brownie-config.yaml`, update the `subscriptionId` under `sepolia` with your own Chainlink VRF v2.5 Subscription ID.

## Usage

### 1. Deploy
Deploy the contract to the Sepolia testnet:
```bash
brownie run scripts/deploy_lottery.py --network sepolia
```
*Note the deployed contract address from the output.*

### 2. Add Consumer
Go to your [Chainlink VRF Subscription Dashboard](https://vrf.chain.link/) and add the deployed contract address as a **Consumer**.

### 3. Run Lottery Cycle
Execute the interaction script to start the lottery, enter it, and end it:
```bash
brownie run scripts/finish_lottery.py --network sepolia
```
This script will:
- Check/Fund the contract with LINK.
- Start the lottery.
- Enter the lottery (requires ETH).
- End the lottery (requests randomness).
- Wait for the VRF callback.

### 4. Check Status
To check the current state, winner, and recent VRF request:
```bash
brownie run scripts/check_status.py --network sepolia
```

## License
This project is licensed under the MIT License.