import requests
import json 
import random
from requests.exceptions import ConnectTimeout
from decimal import Decimal, getcontext
from solana.rpc.api import Client
from solders.pubkey import Pubkey #type:ignore
import time

proxies_list = [
    {"http": "http://nejpopbg:zdtwx7to1lgq@91.123.9.23:6565", "https": "http://nejpopbg:zdtwx7to1lgq@91.123.9.23:6565"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@64.137.8.27:6709", "https": "http://nejpopbg:zdtwx7to1lgq@64.137.8.27:6709"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@104.239.33.131:6486", "https": "http://nejpopbg:zdtwx7to1lgq@104.239.33.131:6486"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@107.173.137.30:6284", "https": "http://nejpopbg:zdtwx7to1lgq@107.173.137.30:6284"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@167.160.180.108:6659", "https": "http://nejpopbg:zdtwx7to1lgq@167.160.180.108:6659"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@217.69.127.127:6748", "https": "http://nejpopbg:zdtwx7to1lgq@217.69.127.127:6748"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@104.222.161.188:6320", "https": "http://nejpopbg:zdtwx7to1lgq@104.222.161.188:6320"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.131.94.130:6117", "https": "http://nejpopbg:zdtwx7to1lgq@45.131.94.130:6117"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.12.179.225:6756", "https": "http://nejpopbg:zdtwx7to1lgq@45.12.179.225:6756"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@109.196.160.167:5913", "https": "http://nejpopbg:zdtwx7to1lgq@109.196.160.167:5913"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@194.116.250.229:6687", "https": "http://nejpopbg:zdtwx7to1lgq@194.116.250.229:6687"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@38.154.227.209:5910", "https": "http://nejpopbg:zdtwx7to1lgq@38.154.227.209:5910"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@207.244.217.83:6630", "https": "http://nejpopbg:zdtwx7to1lgq@207.244.217.83:6630"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.43.65.20:6534", "https": "http://nejpopbg:zdtwx7to1lgq@45.43.65.20:6534"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@107.175.119.244:6772", "https": "http://nejpopbg:zdtwx7to1lgq@107.175.119.244:6772"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@64.137.31.163:6777", "https": "http://nejpopbg:zdtwx7to1lgq@64.137.31.163:6777"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@104.239.43.60:5788", "https": "http://nejpopbg:zdtwx7to1lgq@104.239.43.60:5788"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@161.123.5.200:5249", "https": "http://nejpopbg:zdtwx7to1lgq@161.123.5.200:5249"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@185.118.7.126:6152", "https": "http://nejpopbg:zdtwx7to1lgq@185.118.7.126:6152"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@107.181.141.198:6595", "https": "http://nejpopbg:zdtwx7to1lgq@107.181.141.198:6595"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@184.174.24.103:6679", "https": "http://nejpopbg:zdtwx7to1lgq@184.174.24.103:6679"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@209.242.203.201:6916", "https": "http://nejpopbg:zdtwx7to1lgq@209.242.203.201:6916"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@136.0.207.9:6586", "https": "http://nejpopbg:zdtwx7to1lgq@136.0.207.9:6586"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@138.128.153.201:5235", "https": "http://nejpopbg:zdtwx7to1lgq@138.128.153.201:5235"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@23.236.247.79:8111", "https": "http://nejpopbg:zdtwx7to1lgq@23.236.247.79:8111"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@162.218.208.198:6317", "https": "http://nejpopbg:zdtwx7to1lgq@162.218.208.198:6317"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@43.228.237.99:6045", "https": "http://nejpopbg:zdtwx7to1lgq@43.228.237.99:6045"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@173.211.8.37:6149", "https": "http://nejpopbg:zdtwx7to1lgq@173.211.8.37:6149"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@38.153.140.69:8947", "https": "http://nejpopbg:zdtwx7to1lgq@38.153.140.69:8947"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@45.41.172.218:5961", "https": "http://nejpopbg:zdtwx7to1lgq@45.41.172.218:5961"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@138.128.145.61:5980", "https": "http://nejpopbg:zdtwx7to1lgq@138.128.145.61:5980"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@185.72.240.67:7103", "https": "http://nejpopbg:zdtwx7to1lgq@185.72.240.67:7103"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@154.29.65.148:6256", "https": "http://nejpopbg:zdtwx7to1lgq@154.29.65.148:6256"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@89.40.222.12:6388", "https": "http://nejpopbg:zdtwx7to1lgq@89.40.222.12:6388"},
    {"http": "http://nejpopbg:zdtwx7to1lgq@161.123.215.80:5243", "https": "http://nejpopbg:zdtwx7to1lgq@161.123.215.80:5243"}
]

def special_format(number):
    if number == 0:
        return "0"
    # Set precision high enough to capture small numbers accurately
    getcontext().prec = 50
    number = Decimal(str(number))
    # Handle very small decimals with more than 5 leading zeros
    if 0 < number < Decimal('0.0001'):
        return "⬇️0.0001"
    # Handle other small decimals with fewer than 4 leading zeros
    if 0 < number < 1:
        return f"{number:.4f}".rstrip('0').rstrip('.')
    # Handle larger numbers with suffixes
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        formatted = f"{number / 1_000_000_000:.1f}B"
    elif abs_number >= 1_000_000:
        formatted = f"{number / 1_000_000:.0f}M"
    elif abs_number >= 1_000:
        formatted = f"{number:,.0f}"
    else:
        formatted = f"{number:.4f}".rstrip('0').rstrip('.')
    return formatted

CLIENT = Client("https://api.mainnet-beta.solana.com")

def get_token_supply_mc_cap(mint):
        _supply = CLIENT.get_token_supply(Pubkey.from_string(str(mint)))
        return _supply.value.ui_amount

def get_total_solana_supply(mint):
        _supply = CLIENT.get_token_supply(Pubkey.from_string(str(mint)))
        return _supply.value.ui_amount

def get_solana_token_price(token_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extracting the price of the token (assumes the first market listed)
        price = float(data['pairs'][0]['priceUsd'])
        return price
    else:
        raise Exception("Failed to fetch token data from Dexscreener")




logged_signatures = set()  # Set to store logged signatures
def get_data(url,proxy,token_address):
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
    response = requests.post(url, headers=headers, data=json.dumps(payload),proxies=proxy)
    with open('d.json','w')as file:
        json.dump(response.json(),file,indent=4)
    return response.json()
def get_sec_data(url,proxy,signature):
    headers = {
                "Content-Type": "application/json"
            }
    payload2 = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                '2TKkNocbyEMrnAVxZoPe6uHRSUbQqdnWrpUP2mT1BLY6Wgg5q8BBnns82Vw5LEaPKUnMRdnbpBRJvcCTEFrozndY',
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0
                }
            ]
        }
    response2 = requests.post(url, headers=headers, data=json.dumps(payload2),proxies=proxy)
    with open('q.json','w')as file:
        json.dump(response2.json()['result']['meta']['innerInstructions'],file,indent=4)
    return response2.json()

def moonshot(token_address):
    prev_signature = None
    while True:
        proxy = random.choice(proxies_list)
        print('moonshot')
        try:
            url = "https://api.mainnet-beta.solana.com"
            gotten_loggs = get_data(url,proxy,token_address)
            if gotten_loggs and 'result' in gotten_loggs:
                for trancs in gotten_loggs['result']:
                    signature = trancs['signature']
                    print(signature)
                    if signature not in logged_signatures:
                        logged_signatures.add(signature)
                        try:
                            print('here')
                            other_logg=get_sec_data(url,proxy,signature)
                            data = other_logg
                            messages = data['result']['meta']['logMessages']
                            # print(messages)
                            parsed = data['result']['meta']['innerInstructions'][0]['instructions'][1:]

                            # if 'Program log: Instruction: Swap' in messages:
                            #     new = data['result']['meta']['innerInstructions'][1]['instructions'][3:7]

                            if "Program log: Instruction: Buy" in messages:
                                signer =  data['result']['transaction']['message']['accountKeys']
                                data = data['result']['meta']['innerInstructions'][0]['instructions']
                                actual_authority = []
                                sol_amount = 0
                                token_amount = 0
                                decimal = 0
                                for items in signer:
                                    if items['signer'] == True:
                                        the_signer = items['pubkey']
                                for instance in data:
                                    try:    
                                        info = instance["parsed"]["info"]
                                        authority = info.get("authority")
                                        if authority: 
                                            actual_authority.append(authority)
                                            token_details = info.get("tokenAmount")
                                            if token_details:
                                                token_amount = token_details['uiAmount']
                                                decimal = token_details['decimals']
                                        else:
                                            account =info.get("account")
                                            actual_authority.append(account)
                                            token_details = info.get("tokenAmount")

                                            if token_details:
                                                token_amount = token_details['uiAmount']
                                                decimal = token_details['decimals']
                                        print(actual_authority)
                                    except KeyError:
                                        continue
                                for i in data:
                                    info = i["parsed"]["info"]
                                    try:
                                        if info.get('destination') == actual_authority[-1]:
                                            print(info.get('destination'))
                                            print('this')
                                            lamports = info.get('lamports', 0)
                                            if lamports:
                                                sol_amount = lamports * 10 ** -9
                                                
                                    except KeyError:
                                        continue
                                # Send the SOL and token amount to the Telegram group
                                chart =f"<a href='https://dexscreener.com/solana/{token_address}'>Chart</a>"
                                trend_url=f"https://t.me/BSCTRENDING/5431871"
                                trend=f"<a href='{trend_url}'>Trending</a>"
                                supply_=get_total_solana_supply(token_address)
                                res = get_solana_token_price(token_address)
                                mkt_cap = float(supply_)*float(res)
                                usd_value_bought = res*token_amount
                                if sol_amount or token_amount or the_signer:
                                    # emoji = get_emoji_from_db(chat_id)
                                    thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                                    sign =f"<a href='https://solscan.io/account/{the_signer}'>{thenew_signer}</a>" 
                                    txn = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                                    # buy_step_number = retrieve_group_number(chat_id)
                                   
                                    # message = (
                                    #     f"<b> ✅{name}</b> Buy!\n\n"
                                    #     f"{emoji*calc}\n"
                                    #     f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                    #     f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    #     f"👤{sign}|{txn}\n"
                                    #     f"🔷${special_format(usd_value_bought)}\n"
                                    #     f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                    #     f"🦎{chart} 🔷{trend}"
                                    # )
                                    message = (
                                        f"<b> ✅{'name'}</b> Buy!\n\n"
                                        f"{'🟢'*9}\n"
                                        f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                        f"🪙{special_format(token_amount)} <b>{'symbol'}</b>\n"
                                        f"👤{sign}|{txn}\n"
                                        f"🔷${special_format(usd_value_bought)}\n"
                                        f"MKT Cap : ${special_format(mkt_cap)}\n\n"
                                        f"🦎{chart} 🔷{trend}"
                                    )

                                    try:
                                        if message:
                                            print(message)
                                    except Exception as e:
                                        print('thise',e)
                            else:
                                print('I think it is a failed transaction or sell')

                        except KeyError:
                            print('Sell transaction detected')
                        prev_signature = signature
                        time.sleep(2)  # Wait before retrying

                    else:
                        print('No new transactions')

        except ConnectTimeout:
            print("Connection timed out, retrying...")
            time.sleep(2)  # Wait before retrying

        except KeyError:
            print('restarting .....')
            time.sleep(2)
            moonshot(token_address)
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        #     time.sleep(2)  # Adjust the interval as needed
        #     moonshot(token_address)


moonshot('Fpp3dL4rWAB4TAuvfoK2cstJNqjDCvV9yn9ULT42R62R')