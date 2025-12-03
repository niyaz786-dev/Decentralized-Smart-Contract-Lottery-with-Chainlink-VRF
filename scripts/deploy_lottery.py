from scripts.helpful_scripts import get_account, get_contract, deploy_mocks
from brownie import Lottery, config, network
import time

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

def deploy_lottery():
    account = get_account()
    
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        deploy_mocks()
        lottery = Lottery.deploy(
            get_contract("eth_usd_price_feed").address,
            get_contract("vrf_coordinator").address,
            config["networks"][network.show_active()]["keyhash"],
            config["networks"][network.show_active()]["subscriptionId"],
            {"from": account},
            publish_source=False,
        )
        print(f"Lottery Deployed at: {lottery.address}")
        return lottery
    
    else:
        # Always deploy fresh on testnet
        print("\n📝 Deploying fresh contract with correct key hash...")
        lottery = Lottery.deploy(
            get_contract("eth_usd_price_feed").address,
            get_contract("vrf_coordinator").address,
            config["networks"][network.show_active()]["keyhash"],
            config["networks"][network.show_active()]["subscriptionId"],
            {"from": account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        print(f"\n✅ New Lottery Deployed at: {lottery.address}")
        print("⚠️  IMPORTANT: Add this address as a consumer in your VRF subscription:")
        print(f"   https://vrf.chain.link/sepolia")
        print(f"   Contract Address: {lottery.address}")
        return lottery

def reset_lottery():
    """Reset the lottery state for testing"""
    account = get_account()
    lottery = Lottery[-1]
    
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print("\nResetting lottery state...")
        reset_tx = lottery.resetLottery({"from": account})
        reset_tx.wait(1)
        print("✅ Lottery reset to CLOSED state")

def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("Lottery has started!")

def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You have entered the lottery!")

def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    
    # DEBUG: Check what subscription ID the contract has
    contract_sub_id = lottery.subscriptionId()
    config_sub_id = config['networks'][network.show_active()]['subscriptionId']
    
    print(f"\n🔍 DEBUG INFO:")
    print(f"Contract subscription ID: {contract_sub_id}")
    print(f"Config subscription ID: {config_sub_id}")
    print(f"Match: {contract_sub_id == config_sub_id}")
    
    # Request randomness with manual gas
    print("\nRequesting randomness from VRF...")
    ending_tx = lottery.endLottery({
        "from": account,
        "gas": 500000
    })
    ending_tx.wait(1)
    
    request_id = lottery.requestId()
    print(f"Request ID: {request_id}")
    
    # On local networks, manually trigger the VRF callback
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        print("\n⏱️  LOCAL NETWORK: Triggering VRF callback manually...")
        vrf_coordinator = get_contract("vrf_coordinator")
        random_number = 777
        
        callback_tx = vrf_coordinator.callBackWithRandomness(
            request_id,
            random_number,
            lottery.address,
            {"from": account}
        )
        callback_tx.wait(1)
        print("✅ VRF callback triggered!")
        
    else:
        # On testnet, wait for the actual VRF response
        print("\n⏱️  TESTNET: Waiting for Chainlink VRF response...")
        print("   This can take 5-60 minutes")
        print("   Contract address: " + lottery.address)
        print("   Check on Etherscan: https://sepolia.etherscan.io/address/" + lottery.address)
        
        # Poll for winner (every 60 seconds, max 60 minutes)
        max_wait = 3600  # 60 minutes
        wait_interval = 60
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(wait_interval)
            elapsed += wait_interval
            
            try:
                winner = lottery.winner()
                if winner != "0x0000000000000000000000000000000000000000":
                    print(f"\n✅ WINNER FOUND!")
                    print(f"   Winner: {winner}")
                    print(f"   Time elapsed: {elapsed // 60} minutes")
                    return
            except:
                pass
            
            print(f"   Waiting... ({elapsed // 60}m/{max_wait // 60}m elapsed)")
        
        print("\n❌ Timeout: VRF response not received after 60 minutes")
        return
    
    winner = lottery.winner()
    print(f"\n✅ Winner: {winner}")
    print("Lottery has ended!")


def main():
    print("\n" + "="*60)
    print("LOTTERY DEPLOYMENT & EXECUTION")
    print("="*60)
    print(f"Network: {network.show_active()}\n")
    
    deploy_lottery()
    reset_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
    
    print("\n" + "="*60)
    print("✅ COMPLETE")
    print("="*60)
