import requests
import json
import time
from solders.pubkey import Pubkey #type:ignore
from solana.rpc.api import Client
import struct
import base58
META_DATA_PROGRAM = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
def get_program_address(
        mint, program_id
    ):
       
        return Pubkey.find_program_address(
            [
                b"metadata",
                bytes(Pubkey.from_string(str(program_id))),
                bytes(Pubkey.from_string(str(mint))),
            ],
            Pubkey.from_string(str(program_id)),
        )[0]
def get_account_info(account):
    client = Client("https://api.mainnet-beta.solana.com")

    account_instance =client.get_account_info_json_parsed(
        Pubkey.from_string(str(account))
    )
    return account_instance.value.data

def get_token_info(mint,program_id):
        program_address = get_program_address(str(mint),program_id)
        account_info_instance =get_account_info(program_address)
        token_info = unpack_metadata_account(account_info_instance)
        token_name = token_info["name"]
        token_symbol= token_info["symbol"]

        return token_name , token_symbol
def unpack_metadata_account(data):
    assert data[0] == 4
    i = 1
    source_account = base58.b58encode(
        bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
    )
    i += 32
    mint_account = base58.b58encode(
        bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
    )
    i += 32
    name_len = struct.unpack("<I", data[i : i + 4])[0]
    i += 4
    name = struct.unpack("<" + "B" * name_len, data[i : i + name_len])
    i += name_len
    symbol_len = struct.unpack("<I", data[i : i + 4])[0]
    i += 4
    symbol = struct.unpack("<" + "B" * symbol_len, data[i : i + symbol_len])
    i += symbol_len
    uri_len = struct.unpack("<I", data[i : i + 4])[0]
    i += 4
    uri = struct.unpack("<" + "B" * uri_len, data[i : i + uri_len])
    i += uri_len
    fee = struct.unpack("<h", data[i : i + 2])[0]
    i += 2
    has_creator = data[i]
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack("<I", data[i : i + 4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(
                bytes(struct.unpack("<" + "B" * 32, data[i : i + 32]))
            )
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata["data"]

def pinksale_lunch(token_address):
    prev_res = None
    sol_name,sol_symbol = get_token_info(token_address,META_DATA_PROGRAM)
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
    # print(response.json())
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
            print(signature)
            response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
            res_data = response2.json()
            unit_consumed = res_data['result']['meta']['computeUnitsConsumed']

            # print(res_data)
            # print(res_data)
            with open('k.json','w')as file: 
                    json.dump(res_data,file,indent= 4)
            decimals = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']
            amount_in_symbol = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['amount']
            # if amount_in_symbol != 0:
            #      print(float(amount_in_symbol)*10**-decimals,' symbol')
            another_data = res_data['result']['meta']['innerInstructions'][0]['instructions']
            with open('k.json','w')as file:
                    json.dump(res_data,file,indent= 4)
            print(
                 f'''
Name: {sol_name}
Symbol: {sol_symbol}'''
            )
            sol_deposit_list = []      
            for i in another_data:
                info = i.get("parsed", {}).get("info", {})
                amount = info.get('amount')
                amount_sol = info.get('lamports')
                if amount:
                     authority = info.get('authority')
                     bought = float(amount)*10**-decimals
                     print(f'Amount: {bought} SYMBOL',f'>>> {authority}' )
                if amount_sol:
                     sol_deposit_list.append(float(amount_sol)*10**-decimals) # for the amount in token
            print(f'Deposited in sol: {sol_deposit_list[-1]}')
            total_supply =res_data['result']['meta']['preTokenBalances'][0]['uiTokenAmount']['amount']
            total_supply = float(total_supply)*10**-decimals
            owner =res_data['result']['meta']['preTokenBalances'][0]['owner']
            if total_supply:
                print(f'total supply: {total_supply}')
                print(f'Buyer: {owner}')
        except IndexError:
            try:
                another_data = res_data['result']['meta']['innerInstructions'][0]['instructions']
                for item in another_data:
                    info = item.get("parsed", {}).get("info", {})
                    amount = info.get('lamports')
                    if amount:
                        print(float(amount)*10**-decimals)#*sol price will give you in usd
            except IndexError:
                action = 'Upcomming ..........'
                if action and unit_consumed:
                    print(action)
                    print(f'computeUnitsConsumed: {unit_consumed}')
        except Exception as e:
                print(e)
pinksale_lunch('4GDvsevybnufV1wCZoyFHUSVQ996knZCzhZMP7AnVRef')