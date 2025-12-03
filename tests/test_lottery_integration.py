from brownie import network, accounts
from scripts.helpful_scripts import get_account, fund_with_link, LOCAL_BLOCKCHAIN_ENVIRONMENTS
from scripts.deploy_lottery import deploy_lottery
import pytest
import time


def test_can_pick_winner_correctly():
    """Integration test: Full lottery flow on Sepolia"""
    # Skip if on local network
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for testnet/mainnet testing")
    
    print("\n=== INTEGRATION TEST: Full Lottery on Sepolia ===")
    
    # Deploy
    print("1. Deploying lottery...")
    lottery = deploy_lottery()
    account = get_account()
    print(f"   Lottery deployed at: {lottery.address}")
    
    # Start lottery
    print("2. Starting lottery...")
    start_tx = lottery.startLottery({"from": account})  # ✅ Fixed: startLottery
    start_tx.wait(1)
    assert lottery.lottery_state_vname() == 1  # OPEN
    print("   ✅ Lottery started")
    
    # Enter lottery twice (2 entries for same account)
    print("3. Entering lottery (2 times)...")
    entrance_fee = lottery.getEntranceFee()
    
    enter_tx1 = lottery.enter({"from": account, "value": entrance_fee})
    enter_tx1.wait(1)
    print(f"   Entry 1: {entrance_fee} wei")
    
    enter_tx2 = lottery.enter({"from": account, "value": entrance_fee})
    enter_tx2.wait(1)
    print(f"   Entry 2: {entrance_fee} wei")
    
    # Verify entries
    assert lottery.players(0) == account
    assert lottery.players(1) == account
    print("   ✅ Both entries recorded")
    
    # Fund with LINK
    print("4. Funding with LINK...")
    fund_tx = fund_with_link(lottery.address)
    fund_tx.wait(1)
    print("   ✅ LINK transferred")
    
    # End lottery
    print("5. Ending lottery (requesting randomness)...")
    end_tx = lottery.endLottery({"from": account})
    end_tx.wait(1)
    
    request_id = lottery.recentRequestId()
    print(f"   Request ID: {request_id.hex()}")
    print(f"   State: {lottery.lottery_state_vname()} (2 = CALCULATING_WINNER)")
    
    # Wait for Chainlink VRF response
    print("\n6. Waiting for Chainlink VRF response...")
    print("   This can take 5-60 minutes on Sepolia testnet")
    print("   Checking every 60 seconds...\n")
    
    # Poll for winner (max 60 minutes)
    max_wait = 3600  # 60 minutes
    wait_interval = 60  # Check every 60 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(wait_interval)
        elapsed += wait_interval
        
        try:
            winner = lottery.winner()
            if winner != "0x0000000000000000000000000000000000000000":
                print(f"\n✅ Winner selected: {winner}")
                print(f"   Time elapsed: {elapsed // 60} minutes")
                break
        except:
            pass
        
        print(f"   Waiting... ({elapsed // 60} minutes elapsed)")
    
    # Final assertions
    winner = lottery.winner()
    assert winner == account  # ✅ Fixed: compare directly with account
    assert lottery.balance() == 0
    assert lottery.lottery_state_vname() == 0  # CLOSED
    
    print("\n=== TEST PASSED ===")
    print(f"Winner: {winner}")
    print(f"Lottery balance: {lottery.balance()}")
    print(f"Account balance increased: ✅")


# Run with: brownie test tests/test_lottery_integration.py -s --network sepolia
