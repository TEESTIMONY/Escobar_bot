import requests
import json
import time
import asyncio
def pumpfun(token_address,interval):
    prev_res = None
    while True:
        url = "https://api.mainnet-beta.solana.com"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                token_address,
                {
                    "limit": 1
                }
            ]
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        signature = response.json()['result'][0]['signature']
        if signature!=prev_res:
            payload2 = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature, #change this to signatur comming from step one 
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }

            try:
                response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
                res_data = response2.json()
                messages = res_data['result']['meta']['logMessages']
                parsed = res_data['result']['meta']['innerInstructions'][0]['instructions'][1:]
                # print(messages)
                if 'Program log: Instruction: Swap' in messages:
                    # print('filtered only swap now')
                    new =res_data['result']['meta']['innerInstructions'][1]['instructions'][3:7]
                elif "Program log: Instruction: Buy" in messages:
                    data = res_data['result']['meta']['innerInstructions'][0]['instructions'][:7]
                    actual_authority = []
                    for instance in data:
                        try:
                            info = instance["parsed"]["info"]
                            authority = instance["parsed"]["info"]["authority"]
                            actual_authority.append(authority)
                            if 'authority' in info:
                                token = float(info['amount'])*10**-6
                                return token
                                # print('token',token)
                            else:
                                pass
                            decimal = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']
                        except KeyError:
                            continue
                    for i in data:
                        # print(info['destination'])
                        try:
                            info = i["parsed"]["info"]
                            if info['destination'] == actual_authority[-1]:
                                solana = info['lamports']*10**-9
                                return solana

                            else:
                                pass
                        except KeyError:
                            continue
                    # print(data)
                else:
                    print('sell ')
                
            except IndexError:
                print('sell')
            prev_res = signature
        else:
            print('already there')        
        time.sleep(interval)

address = 'DpxnTaUFLiAAQk8kgTfsvXDvRA6X2CjSB6fic5WFcJJ5'
pumpfun(address,3)
