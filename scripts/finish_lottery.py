from brownie import Lottery, accounts, config, network, interface
import time


def get_account():
    """Return the deployer/account from the private key in .env."""
    return accounts.add(config["wallets"]["from_key"])


def ensure_link_balance(lottery_address, min_balance=0.2 * 10**18):
    """Check LINK balance of the contract and fund it if below `min_balance`.
    Uses the helper `fund_with_link` from `helpful_scripts.py`.
    """
    link_token = interface.LinkTokenInterface(
        config["networks"][network.show_active()]["link_token"]
    )
    balance = link_token.balanceOf(lottery_address)
    print(f"Current LINK balance: {balance}")
    if balance < min_balance:
        print("Funding contract with LINK...")
        from scripts.helpful_scripts import fund_with_link
        fund_with_link(lottery_address, amount=min_balance * 2)  # add a safety margin
        # Re‑check after funding
        balance = link_token.balanceOf(lottery_address)
        print(f"New LINK balance: {balance}")
    else:
        print("Sufficient LINK balance present.")


def finish_lottery():
    acct = get_account()
    lottery = Lottery[-1]
    print(f"Interacting with Lottery at {lottery.address}")

    # 1️⃣ Ensure the contract has enough LINK before any VRF call
    ensure_link_balance(lottery.address)

    # 2️⃣ Start the lottery if it is CLOSED (enum value 1)
    state = lottery.lottery_state()
    print(f"Current lottery state (0=OPEN,1=CLOSED,2=CALCULATING): {state}")
    if state == 1:  # CLOSED
        print("Starting lottery...")
        try:
            tx = lottery.startLottery({"from": acct, "gas_price": "0.001 gwei"})
            tx.wait(1)
            print("Lottery started!")
        except Exception as e:
            print(f"Error starting lottery: {e}")
            return
    else:
        print("Lottery already open or calculating – skipping start.")

    # 3️⃣ Enter the lottery
    print("Entering lottery...")
    try:
        value = lottery.getEntranceFee() + 100000000  # small buffer
        tx = lottery.enter({"from": acct, "value": value, "gas_price": "0.001 gwei"})
        tx.wait(1)
        print("Entered lottery.")
    except Exception as e:
        print(f"Error entering lottery: {e}")
        return

    # 4️⃣ End the lottery – request randomness
    print("Ending lottery (requesting randomness)...")
    try:
        tx = lottery.endLottery({"from": acct, "gas": 800000, "gas_price": "0.001 gwei"})
        tx.wait(1)
        print("Lottery ended – VRF request sent.")
    except Exception as e:
        print(f"Error ending lottery: {e}")
        if hasattr(e, 'revert_msg'):
            print(f"Revert reason: {e.revert_msg}")
        return

    # 5️⃣ Wait for the winner (polling)
    print("Waiting for VRF to pick a winner (up to 1 hour)...")
    max_wait = 7200  # 2 hours
    start = time.time()
    while time.time() - start < max_wait:
        try:
            # When winner is picked the state returns to CLOSED (1)
            if lottery.lottery_state() == 1 and lottery.winner() != "0x0000000000000000000000000000000000000000":
                print(f"Winner selected: {lottery.winner()}")
                print(f"Randomness used: {lottery.randomness()}")
                return
        except Exception:
            pass
        print("Waiting...", end="\r")
        time.sleep(15)
    print("Timed out waiting for VRF response.")


def main():
    finish_lottery()
