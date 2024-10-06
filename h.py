import requests
import json
import time
def get_moonshot_trades(token_address):
    logged_hash = set()
    while True:
        response = requests.get(
            f"https://api.moonshot.cc/trades/v1/latest/solana/{token_address}",
            headers={},
        )
        datas = response.json()[:3]
        for data in reversed(datas):
            txn_hash = data['txnId']
            if txn_hash not in logged_hash:
                logged_hash.add(txn_hash)
                token_amount = data['amount0']
                sol_Amount = data['amount1']
                price_in_usd = data['volumeUsd']
                activity_type =data['type']
                print(float(token_amount))
                print(float(sol_Amount))
                print(float(price_in_usd))
                print((activity_type))
            else:
                print('already logged')
        with open('q.json','w')as file:
            json.dump(data,file,indent=4)
        # return token_amount ,sol_Amount , price_in_usd , activity_type
        time.sleep(3)

# get_moonshot_trades('9SoUhTCK7DaFgyWue2HCvtAUJLP4i5LCP74gZ5CAW4uN')


import requests


