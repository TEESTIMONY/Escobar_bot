import requests
import json
import time

def get_latest_signature(token_address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [token_address, {"limit": 1}]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['result'][0]['signature']
    except (requests.exceptions.HTTPError, IndexError) as e:
        print(f"Error fetching signature: {e}")
        return None

def get_transaction_details(signature):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
        ]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching transaction: {e}")
        return None

def parse_transaction_data(res_data):
    try:
        messages = res_data['result']['meta']['logMessages']
        if 'Program log: Instruction: Swap' in messages:
            sol_ana = res_data['result']['meta']['innerInstructions'][1]['instructions'][3]['parsed']['info']['lamports'] * 10**-9
            token_ = float(res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['amount']) * 10**-res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']
            return sol_ana, token_
        elif "Program log: Instruction: Buy" in messages:
            data = res_data['result']['meta']['innerInstructions'][0]['instructions'][:7]
            sol_ana = 0
            token_ = 0
            actual_authority = []

            for instance in data:
                try:
                    info = instance["parsed"]["info"]
                    authority = info["authority"]
                    actual_authority.append(authority)

                    if 'authority' in info:
                        token_ = float(info['amount']) * 10**-6

                except KeyError:
                    continue

            for i in data:
                try:
                    info = i["parsed"]["info"]
                    if info['destination'] == actual_authority[-1]:
                        sol_ana = info['lamports'] * 10**-9
                except KeyError:
                    continue

            return sol_ana, token_
        else:
            print("Failed transaction or sell detected")
            return None, None
    except (KeyError, IndexError) as e:
        print(f"Error parsing transaction: {e}")
        return None, None

def pumpfun(token_address):
    prev_res = None
    while True:
        signature = get_latest_signature(token_address)
        if not signature or signature == prev_res:
            print('No new transaction or already processed')
            time.sleep(5)
            continue

        res_data = get_transaction_details(signature)
        if res_data:
            sol_ana, token_ = parse_transaction_data(res_data)
            if sol_ana is not None and token_ is not None:
                return f'Solana amount: {sol_ana}, Token amount: {token_}'

        prev_res = signature
        time.sleep(5)

address = 'CLLi84FzVDn9FFsF3SB4veAGFVwG3AWTQn26F4GVpump'
s=pumpfun(address)
print(s)