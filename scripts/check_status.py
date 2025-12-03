from brownie import Lottery, config, network, interface

def main():
    lottery = Lottery[-1]
    print(f"Contract address: {lottery.address}")
    print(f"Lottery state: {lottery.lottery_state()} (0=OPEN,1=CLOSED,2=CALCULATING)")
    print(f"Winner (if any): {lottery.winner()}")
    print(f"Request ID: {lottery.requestId()}" )
    # LINK balance
    link = interface.LinkTokenInterface(config["networks"][network.show_active()]["link_token"])
    bal = link.balanceOf(lottery.address)
    print(f"LINK balance: {bal}")
    # subscription ID stored in contract
    print(f"Contract subscription ID: {lottery.subscriptionId()}")
