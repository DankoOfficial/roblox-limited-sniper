import requests
import uuid
import time
import sys
import random
import ctypes
import os

from pystyle import *
from colorama import Fore, Back

class checks:
    success = 0
    fail = 0
    bought = 0
    lastChecked = None
    lastCheckedPrice = None

# You must provide your actual Roblox .ROBLOSECURITY cookie and your Roblox User ID.
ROBLOSECURITY = ''
discord_webhook = ''

# Create a session and set the cookie
session = requests.Session()
session.cookies[".ROBLOSECURITY"] = ROBLOSECURITY

def update_csrf_token(sess, url="https://auth.roblox.com/v2/logout"):
    """
    Updates the session's CSRF token.
    """
    r = sess.post(url, cookies={".ROBLOSECURITY": ROBLOSECURITY})
    csrf = r.headers.get("x-csrf-token")
    if csrf:
        sess.headers["X-CSRF-Token"] = csrf
    return csrf

def accInfo():
    return session.get('https://users.roblox.com/v1/users/authenticated').json()

_ = accInfo()
purchaser_id = _['id']
purchaser_username = _['name']
purchaser_robux = session.get(f'https://economy.roblox.com/v1/users/{purchaser_id}/currency').json()['robux']

update_csrf_token(session)

def fetch_item_details(target_id):
    """
    Fetches the item details JSON from the Roblox economy API.
    """
    url = f"https://economy.roblox.com/v2/assets/{target_id}/details"
    r = session.get(url)
    if r.status_code != 200:
        print(f"Failed to fetch item details. Status code: {r.status_code}")
        return None
    return r.json()

def monitor_multiple_items(items):
    print("\nStarting monitoring for multiple Limiteds...\n")
    os.system('cls')
    a = ', '.join(i["name"] for i in items)

    while True:
        _logo_()
        print()
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Logged in as: {Col.white}{purchaser_username}{Fore.RESET}')
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Robux balance: {Col.white}{purchaser_robux} R${Fore.RESET}')
        print()
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Sniping: {Col.white}{len(items)} item(s) ({a}){Fore.RESET}')
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Successful checks: {Col.green}{checks.success}{Fore.RESET}')
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Failed checks: {Col.red}{checks.fail}{Fore.RESET}')
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Last check: {Col.light_green}{checks.lastChecked} for {checks.lastCheckedPrice} R${Fore.RESET}')
        print()
        print(f'                                            {Col.light_blue}>>{Fore.RESET} Items sniped: {Col.green}{checks.bought}{Fore.RESET}')

        updateTitle(f'RoSniper | @DankoOfficial | Roblox Limited Sniper | Current Task: Monitoring [Checked: {checks.success} - Retries: {checks.fail} - Bought: {checks.bought}] | Last checked: {checks.lastChecked} ({checks.lastCheckedPrice} R$)')
        item = random.choice(items)

        if item["sniped_count"] >= item["target_quantity"]:
            continue  # Skip if already fulfilled

        url = f"https://apis.roblox.com/marketplace-sales/v1/item/{item['collectible_id']}/resellers?limit=10"
        try:
            r = requests.get(url)
            if r.status_code != 200:
                checks.fail+=1
                time.sleep(1)
                continue
            listings = r.json().get("data", [])
            for listing in listings:
                price = listing.get("price")
                if price is None:
                    checks.fail+=1
                    continue
                if price <= item["target_price"]:
                    print(f"[{item['name']}] Found for {price} Robux!")
                    if buy_item(listing, item["collectible_id"]):
                        item["sniped_count"] += 1
                        checks.bought+=1
                        print(f"✅ Sniped {item['name']} ({item['sniped_count']}/{item['target_quantity']})")

                        # Optional: send to Discord
                        requests.post(
                            discord_webhook,
                            json={
                                "content": f"Sniped {item['name']} for {price} Robux ({item['sniped_count']}/{item['target_quantity']})",
                                "embeds": None,
                                "attachments": []
                            }
                        )
            checks.lastChecked = item['name']
            checks.lastCheckedPrice = price

            # Check if all items are done
            if all(i["sniped_count"] >= i["target_quantity"] for i in items):
                print("\nWohoo! All targets achieved. Exiting...\n")
                input("Press Enter to close.")
                sys.exit(0)

            checks.success+=1
            time.sleep(0.85)
            os.system('cls')
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

def buy_item(listing, collectible_item_id):
    """
    Attempts to buy the item using the listing's details.
    Constructs the purchase payload and sends the POST request.
    """
    purchase_url = f"https://apis.roblox.com/marketplace-sales/v1/item/{collectible_item_id}/purchase-resale"
    payload = {
        "collectibleItemId": collectible_item_id,
        "expectedCurrency": 1,
        "expectedPrice": listing["price"],
        "expectedPurchaserId": purchaser_id,
        "expectedPurchaserType": "User",
        "expectedSellerId": listing["seller"]["sellerId"],
        "expectedSellerType": "User",
        "idempotencyKey": str(uuid.uuid4()),
        "collectibleItemInstanceId": listing["collectibleItemInstanceId"],
        "collectibleProductId": listing["collectibleProductId"]
    }
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.headers.get("X-CSRF-Token", "")
    }
    # Make the purchase request
    r = session.post(purchase_url, json=payload, headers=headers)
    # If the token was outdated, update it and try once more.
    if r.status_code == 403:
        update_csrf_token(session)
        headers["X-CSRF-Token"] = session.headers.get("X-CSRF-Token", "")
        r = session.post(purchase_url, json=payload, headers=headers)
    if r.status_code == 200:
        return True
    else:
        print(f"Purchase failed (status code {r.status_code}): {r.text}")
        return False

# ====== Main Flow ======

def updateTitle(title):
    return ctypes.windll.kernel32.SetConsoleTitleW(title)


def _logo_():
    S = r"""
                                            ┏━┓ ┳┓    ┓   ┏┓┏┏• •  ┓ - @DankoOfficial
                                            ┃┗┛ ┃┃┏┓┏┓┃┏┏┓┃┃╋╋┓┏┓┏┓┃ - On
                                            ┗━┛ ┻┛┗┻┛┗┛┗┗┛┗┛┛┛┗┗┗┗┻┗ - Github"""
    print(Center.XCenter(Colorate.Vertical(Col.blue_to_purple, S, 6))+Fore.RESET)

def main():
    # Step 1: Get multiple item IDs from the user
    _logo_()
    updateTitle('RoSniper | @DankoOfficial | Roblox Limited Sniper | Current Task: Main Menu')
    item_configs = []
    try:
        item_count = int(input(f"How many limited items do you want to monitor?: ").strip())
    except ValueError:
        print("Invalid number.")
        sys.exit(1)

    for i in range(item_count):
        print(f"\nEnter details for item #{i+1}:")
        item_id = input("Item ID: ").strip()
        try:
            target_price = int(input("Target snipe price: ").strip())
            target_quantity = int(input("How many to snipe from this item?: ").strip())
        except ValueError:
            print("Invalid input.")
            sys.exit(1)

        details = fetch_item_details(item_id)
        while not details:
            print('Retrying...')
            details = fetch_item_details(item_id)
            time.sleep(3)
        item_name = details.get("Name", f"Item {item_id}")
        collectible_item_id = details.get("CollectibleItemId")
        is_limited = details.get("CollectiblesItemDetails", {}).get("IsLimited", False)

        if not is_limited or not collectible_item_id:
            print(f"Skipping {item_name} — not a Limited or missing data.")
            continue

        item_configs.append({
            "item_id": item_id,
            "name": item_name,
            "collectible_id": collectible_item_id,
            "target_price": target_price,
            "target_quantity": target_quantity,
            "sniped_count": 0
        })

    if not item_configs:
        print("No valid Limited items were provided.")
        sys.exit(1)

    # Step 2: Begin monitoring
    monitor_multiple_items(item_configs)


if __name__ == "__main__":
    main()
