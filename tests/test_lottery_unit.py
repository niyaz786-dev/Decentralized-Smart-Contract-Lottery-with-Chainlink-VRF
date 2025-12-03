from brownie import accounts, network, config, exceptions
from web3 import Web3
from scripts.helpful_scripts import get_account, get_contract
from scripts.deploy_lottery import deploy_lottery, start_lottery, fund_with_link
import pytest

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")

    # Arrange
    lottery = deploy_lottery()
    
    # Act
    expected_entry_fee = Web3.to_wei(0.014, "ether")
    entrance_fee = lottery.getEntranceFee()
    
    # Assert
    assert expected_entry_fee <= entrance_fee
    print(f"✅ Entrance fee test passed: {entrance_fee}")


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")

    # Arrange
    lottery = deploy_lottery()
    
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})
    
    print("✅ Can't enter unless started test passed")


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    
    # Assert
    assert lottery.players(0) == account
    print(f"✅ Start and enter test passed: Player = {account}")


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)
    
    # Act
    lottery.endLottery({"from": account})
    
    # Assert
    assert lottery.lottery_state_vname() == 2  # CALCULATING_WINNER state
    print("✅ End lottery test passed")


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    
    # Enter 3 players
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    
    fund_with_link(lottery.address)
    
    # Get starting balances
    starting_balance_account = account.balance()
    starting_balance_lottery = lottery.balance()
    
    # Calculate expected winner BEFORE endLottery
    STATIC_RANDOM_NUMBER = 777
    expected_winner_index = STATIC_RANDOM_NUMBER % 3
    expected_winner = lottery.players(expected_winner_index)  # ✅ Read BEFORE reset
    
    # Act - End lottery
    ending_tx = lottery.endLottery({"from": account})
    
    # Read recentRequestId from contract
    request_id = lottery.recentRequestId()
    
    # Simulate Chainlink VRF callback
    vrf_coordinator = get_contract("vrf_coordinator")
    
    vrf_coordinator.callBackWithRandomness(
        request_id,
        STATIC_RANDOM_NUMBER,
        lottery.address,
        {"from": account}
    )
    
    # Assert
    assert lottery.winner() == expected_winner
    assert lottery.balance() == 0
    expected_winner_account = accounts.at(expected_winner)
    assert expected_winner_account.balance() > starting_balance_account
    
    print(f"✅ Winner test passed: Winner = {expected_winner}")
