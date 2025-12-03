from brownie import Lottery

def main():
    if len(Lottery) > 0:
        print(f"Latest Lottery Address: {Lottery[-1].address}")
    else:
        print("No Lottery contract found.")
