# we want the result to be 0.012
from brownie import Lottery, accounts, config, network, exceptions
from web3 import Web3

def test_get_entrance_fee():
    account = accounts[0]
    price_feed = config["networks"][network.show_active()]["eth_usd_price_feed"]
    print(f"Using price feed: {price_feed}")
    lottery = Lottery.deploy(price_feed, {"from": account})
    
    try:
        entrance_fee = lottery.getEntranceFee()
        print(f"Entrance fee: {entrance_fee}")
    except Exception as e:
        print(f"Error in getEntranceFee: {e}")
        raise e

    assert entrance_fee > Web3.toWei(0.010, "ether")


