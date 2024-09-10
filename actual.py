#============= imports =======================#
import logging
from telegram import Chat, ChatMember, ChatMemberUpdated, Update,InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,ChatMemberHandler,CallbackQueryHandler,ConversationHandler,MessageHandler,filters
import re
import threading
from web3 import Web3
import requests
import time
import mysql.connector
from mysql.connector import Error
import asyncio
from solana.rpc.api import Client
from solders.pubkey import Pubkey #type:ignore
from solana.rpc.websocket_api import connect
from solana.rpc.websocket_api import RpcTransactionLogsFilterMentions
from websockets.exceptions import ConnectionClosedError
from solders.rpc.responses import LogsNotification,SubscriptionResult #type:ignore
from solders.signature import Signature #type:ignore
from pycoingecko import CoinGeckoAPI        
from solana.rpc.types import MemcmpOpts
from typing import List, Union
import base58
import struct
stop_events = {}
CG = CoinGeckoAPI()
CLIENT = Client("https://api.mainnet-beta.solana.com")
RAYDIUM_POOL = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_AUTHORITY = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
META_DATA_PROGRAM = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
WRAPPED_SOL = "So11111111111111111111111111111111111111112"

SEND_MEDIA = 'SEND_MEDIA'
# Enable logging
with open('passsss.txt','r') as f:
    PASSWORD=f.read()
import mysql.connector
from mysql.connector import Error
import io
def download_file(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Failed to download file")

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None
db_config = {
    'user': 'Delobots',
    'password': 'mysqlforbot2024',
    'host': 'Delobots.mysql.pythonanywhere-services.com',
    'database': 'Delobots$Escobar_prop',
}



def save_or_update_group_buy_number(group_id, number):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO group_numbers (group_id, number)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
        number = VALUES(number)
    """, (group_id, number))
    conn.commit()
    cursor.close()
    conn.close()

def retrieve_group_number(group_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM group_numbers WHERE group_id = %s", (group_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_account_info(account):
    client = Client("https://api.mainnet-beta.solana.com")

    account_instance =client.get_account_info_json_parsed(
        Pubkey.from_string(str(account))
    )
    return account_instance.value.data

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

def get_token_info(mint,program_id):
        program_address = get_program_address(str(mint),program_id)
        account_info_instance =get_account_info(program_address)
        token_info = unpack_metadata_account(account_info_instance)
        token_name = token_info["name"]
        token_symbol= token_info["symbol"]

        return token_name , token_symbol

def calculate_asset_value(amount):
    price_per_sol = CG.get_price("solana", "usd")["solana"]["usd"]
    return float(amount) * float(price_per_sol)

def format_number(number):
    if abs(number) >= 1e15:
        return f"{number / 1e15:.2f}Q"
    elif abs(number) >= 1e12:
        return f"{number / 1e12:.2f}T"
    elif abs(number) >= 1e9:
        return f"{number / 1e9:.2f}B"
    elif abs(number) >= 1e6:
        return f"{number / 1e6:.2f}M"
    elif abs(number) >= 1e3:
        return f"{number / 1e3:.2f}K"
    elif number < 1000 and number >=1:
        return f"{number:.2f}"
    elif number < 1:
        return f"{number:.6f}"
    
def get_token_supply(mint):
        _supply = CLIENT.get_token_supply(Pubkey.from_string(str(mint)))
        return _supply.value.ui_amount
    
def fetch_mint_pool_amm_id(mint):
        memcmp_opts_1 = MemcmpOpts(offset=400, bytes=str(mint))
        memcmp_opts_2 = MemcmpOpts(offset=432, bytes=str(WRAPPED_SOL))
        filters: List[Union[int, MemcmpOpts]] = [752, memcmp_opts_1, memcmp_opts_2]
        resp = CLIENT.get_program_accounts(
            Pubkey.from_string(str(RAYDIUM_POOL)),
            encoding="base64",
            filters=filters,
        )
        return resp.value[0].pubkey




def format_for_frontend(number):
    # Consider scientific notation for numbers outside the range [1, 1000)
    if abs(number) < 1 or abs(number) >= 1000:
        rounded_number = "{:.1e}".format(number)
        mantissa, exponent = rounded_number.split('e')
        return f"{mantissa} × 10^{int(exponent)}"
    else:
        return str(number)
def format_with_unicode(number):
    superscripts = {
        '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
        '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }

    if abs(number) < 1 or abs(number) >= 1000:
        rounded_number = "{:.1e}".format(number)
        mantissa, exponent = rounded_number.split('e')
        
        # Convert exponent digits to superscript
        unicode_exponent = ''.join(superscripts[char] for char in str(int(exponent)))
        
        return f"{mantissa} × 10{unicode_exponent}"
    else:
        return str(number)

def get_emoji_from_db(chat_id: int) -> str:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emoji FROM emojis
        WHERE chat_id = %s
    """, (chat_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return result[0]
    return None


def save_or_update_media_in_db(file_id: str, file_type: str, chat_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO media (file_id, file_type, chat_id)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        file_id = VALUES(file_id),
        file_type = VALUES(file_type),
        created_at = CURRENT_TIMESTAMP
    """, (file_id, file_type, chat_id))
    conn.commit()
    cursor.close()
    conn.close()

def save_emoji_to_db(emoji: str, chat_id: int) -> None:
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emojis (emoji, chat_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            emoji = VALUES(emoji),
            created_at = CURRENT_TIMESTAMP
        """, (emoji, chat_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(e)

def check_group_exists(group_id):
    try:
        for_connect = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )
        # Establish a database connection
        
        if for_connect.is_connected():
            print("Connected to the database")

            cursor = for_connect.cursor()

            # Define the SQL command to check if the group exists
            check_query = """
            SELECT COUNT(*)
            FROM chat_info
            WHERE chat_id = %s;
            """

            # Execute the SQL command
            cursor.execute(check_query, (group_id,))

            # Fetch the result
            result = cursor.fetchone()
            count = result[0]

            if count > 0:
                return 'good'
            else:
                return 'bad'

    except Error as e:
        print(f"Error: {e}")
    finally:
        if for_connect.is_connected():
            cursor.close()
            for_connect.close()
            print("Database connection closed.")


def fetch_token_address(group_id):
    try:
        # Establish a database connection

        connection = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )
        
        if connection.is_connected():
            print("Connected to the database")

            cursor = connection.cursor()

            # Define the SQL command to fetch the token address
            fetch_query = """
            SELECT token_address
            FROM chat_info
            WHERE chat_id = %s;
            """

            # Execute the SQL command
            cursor.execute(fetch_query, (group_id,))

            # Fetch the result
            result = cursor.fetchone()

            if result:
                token_address = result[0]
                return token_address
            else:
                return 'No token yet'

    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

def delete_chat_id(chat_id):
    try:
        # Establish the connection
        to_delete = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )

        if to_delete.is_connected():
            cursor = to_delete.cursor()

            # SQL query to delete a row by chat_id
            sql_delete_query = """DELETE FROM chat_info WHERE chat_id = %s"""
            cursor.execute(sql_delete_query, (chat_id,))

            # Commit the transaction
            to_delete.commit()

            print(f"Row with chat_id = {chat_id} deleted successfully.")
        else:
            print('didnt happen')
    except Error as e:
        print(f"Error: {e}")

    finally:
        if to_delete.is_connected():
            cursor.close()
            to_delete.close()


def insert_user(telegram_id,given_address):
    try:
        # Connect to the database
        to_connect = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )

        if to_connect.is_connected():
            print("Connected to the database")

            cursor = to_connect.cursor()

            # Define the SQL command to insert a record
            insert_query = """
            INSERT INTO chat_info (chat_id, token_address)
            VALUES (%s, %s);
            """

            # Execute the SQL command
            cursor.execute(insert_query, (telegram_id, given_address))

            # Commit the transaction
            to_connect.commit()
            print("User data inserted successfully.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if to_connect.is_connected():
            cursor.close()
            to_connect.close()
            print("Database connection closed.")

# Example usage
def save_media_to_db(chat_id, media_type, media_content):
    try:
        for_save = mysql.connector.connect(
            host='Delobots.mysql.pythonanywhere-services.com',
            user='Delobots',
            password='mysqlforbot2024',
            database='Delobots$Escobar_prop'
        )

        if for_save.is_connected():
            cursor = for_save.cursor()
            sql_insert_query = """INSERT INTO media (chat_id, media_type, media) VALUES (%s, %s, %s)"""
            cursor.execute(sql_insert_query, (chat_id, media_type, media_content))
            for_save.commit()
            print("Media saved successfully.")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if for_save.is_connected():
            cursor.close()
            for_save.close()

def fetch_media_from_db(chat_id: int):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, file_type FROM media WHERE chat_id = %s ORDER BY created_at DESC LIMIT 1", (chat_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

UNISWAP_FACTORY_ADDRESS = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
PANCAKESWAP_FACTORY_ADDRESS = Web3.to_checksum_address('0xca143ce32fe78f1f7019d7d551a6402fc5350c73')

# Uniswap V2 Factory ABI (simplified version)
UNISWAP_FACTORY_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''
# ERC-20 token ABI (simplified version for name and symbol)
ERC_20_ABI = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''

BASE_ERC_20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "name": "",
                "type": "uint8"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]


UNISWAP_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "name": "_reserve0",
                "type": "uint112"
            },
            {
                "name": "_reserve1",
                "type": "uint112"
            },
            {
                "name": "_blockTimestampLast",
                "type": "uint32"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

PANCAKESWAP_FACTORY_ABI = '''
[
    {
        "constant": true,
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address"
            }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
'''

PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

BSC_PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

CONTRACT_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

BASE_UNISWAP_FACTORY_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

BASE_UNISWAP_FACTORY_ADDRESS = '0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6' 

BASE_WETH_ADDRESS = '0x4200000000000000000000000000000000000006'

BASE_CONTRACT_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

ETH_USD_ABI = '[{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}]'
PANCAKE_FACTORY_ADDRESS = Web3.to_checksum_address('0xca143ce32fe78f1f7019d7d551a6402fc5350c73')
# WBNB token address on BSC
WBNB_ADDRESS = Web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')

# WBNB address (checksum format)
ETH_USD_ADDRESS = Web3.to_checksum_address('0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419')
# WETH token address on Uniswap V2
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
CHOOSING,FOR_ETH,FOR_BSC,FOR_BASE,FOR_TON,FOR_SOL,SEND_MEDIA = range(7)
def is_valid_ethereum_address(address: str)-> bool:
    return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None

infura_url = 'https://mainnet.infura.io/v3/9a7cbdec6fb8401b99acf17aac6ad0d3'
web3 = Web3(Web3.HTTPProvider(infura_url))
# Connect to a BSC node
bsc_url = 'https://bsc-dataseed.binance.org/'
bsc_web3 = Web3(Web3.HTTPProvider(bsc_url))

base_again_url = "https://base-mainnet.g.alchemy.com/v2/UfcBQ-1JALhYM8g88BESGng2WnnkHWnd"  # Update with the actual Base RPC URL
base_again_web3 = Web3(Web3.HTTPProvider(base_again_url))

base_rpc_url = 'https://mainnet.base.org'
base_web3 = Web3(Web3.HTTPProvider(base_rpc_url))

# Check connection  
if web3.is_connected():
    print("Connected to Ethereum network")  #probably write all the code her to avoid errors
else:
    print("Connection failed")

# Check connection
if bsc_web3.is_connected():
    print("Connected to Binance Smart Chain")
else:
    print("Connection failed")

if base_web3.is_connected():
    print("Connected to Base Smart Chain")
else:
    print("Connection failed")

if base_again_web3.is_connected():
    print("Connected to Base another Smart Chain")
else:
    print("Connection failed")

base_uniswap_factory_contract = base_web3.eth.contract(address=BASE_UNISWAP_FACTORY_ADDRESS, abi=BASE_UNISWAP_FACTORY_ABI)
uniswap_factory_contract = web3.eth.contract(address=UNISWAP_FACTORY_ADDRESS, abi=UNISWAP_FACTORY_ABI)

def get_ton_details(token_address):
    url= f'https://api.dexscreener.com/latest/dex/pairs/ton/{token_address}'
    data = requests.get(url)
    resp=data.json()
    resp = resp['pairs'][0]
    pair_address = resp['pairAddress']
    name = resp['baseToken']['name']
    symbol = resp['baseToken']['symbol']
    price_usd = resp['priceUsd']
    mkt_cap = resp['fdv']
    native_price = resp['priceNative']

    return pair_address , name ,symbol ,price_usd , mkt_cap,resp,native_price


async def hunt_ton(token_address,context,chat_id,stop_event):
    try:
        previous_response = None
        
        while not stop_event.is_set():
            pair_address,name,symbol,price_usd,mktcap,data,native=get_ton_details(token_address)
            # pair_address = 'EQCCsJOGdUdSGq0ambJFgSptdHfDPkaQlKlLIKTqtazhhcps'
            url = f'https://api.dedust.io/v2/pools/{token_address}/trades'
            data = requests.get(url)
            result = data.json()
            result = result[-1]
            response = f'''amount_in = {result['amountIn']}
        amount_out = {result['amountOut']}'''
            # Check if the current response is different from the previous one
            print(response)
            if response != previous_response:
                if result['assetIn']['type'] == 'native':
                    print('BUY!!')
                    print(result)
                    print(response)
                    print('')
                    previous_response = response
                    ton_bought = float(result['amountIn'])*10**-9
                    token_bought = float(result['amountOut'])*10**-9
                    # price_usd = float(price_usd)*10**-9
                    usd_value_bought = float(token_bought) * float(price_usd)
                    trend_url=f"https://t.me/BSCTRENDING/5431871"
                    chart_url=f"https://dexscreener.com/ton/{pair_address}"
                    trend=f"<a href='{trend_url}'>Trending</a>"
                    chart=f'<a href="{chart_url}">Chart</a>'
                    emoji = get_emoji_from_db(chat_id)
                    buy_step_number = retrieve_group_number(chat_id)
                    if buy_step_number == None:
                        buuy = 10
                    else:
                        buuy = buy_step_number
                    calc = int(usd_value_bought/buuy)
                    print('native',native)
                    print('usd',price_usd)
                    if emoji:
                        message = (
                            f"<b>✅{name}</b> BUY!\n\n"
                            f"{emoji*calc}\n"
                            f"💵{round(float(ton_bought),2)}<b>TON</b>\n"
                            f"🪙{round(float(token_bought),2)} <b>{symbol}</b>\n"
                            f"🔷${round(usd_value_bought,2)}\n"
                            f"🧢MKT Cap : ${format_number(mktcap)}\n\n"
                            f"🦎{chart} 🔷{trend}"
                        )
                    else:
                        message = (
                            f"<b>✅{name}</b> BUY!\n\n"
                            f"{'🟢'*calc}\n"
                            f"💵{float(ton_bought)*10**-9}<b>TON</b>\n"
                            f"🪙{round(float(token_bought)*10**-9,2)} <b>{symbol}</b>\n"
                            f"🔷${usd_value_bought}\n"
                            f"🧢MKT Cap : ${format_number(mktcap)}\n\n"
                            f"🦎{chart} 🔷{trend}"
                        )

                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id, file_type = media
                        if file_type == 'photo':
                            await context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML')
                        elif file_type == 'gif':
                            await context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML')

                    else:
                        print("No media found in the database for this group.")
                        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML',disable_web_page_preview=True)
            await asyncio.sleep(2)
    
    except Exception as e:
        print('ton',e)
        print("Connection closed, reconnecting...")
        await asyncio.sleep(5)
        await hunt_ton(token_address,context,chat_id)

def start_ton_logging(token_address,context,chat_id):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()

    stop_event = stop_events[chat_id]
    stop_event.clear()
    asyncio.run_coroutine_threadsafe(
        hunt_ton(token_address,context,chat_id,stop_event),
        asyncio.get_event_loop()
    )




# Function to get pair address
def get_pair_address(token_address):
    pair_address = uniswap_factory_contract.functions.getPair(token_address, WETH_ADDRESS).call()
    return pair_address
# Function to get token name and symbol
def get_token_details(token_address):
    token_contract = web3.eth.contract(address=token_address, abi=ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimal= token_contract.functions.decimals().call()
    return name, symbol,decimal

def get_base_token_details(token_address):
    token_contract = base_web3.eth.contract(address=token_address, abi=BASE_ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimals = token_contract.functions.decimals().call()
    return name, symbol, decimals

#base 
def get_base_pair_address(token_address):
    base_pair_address = base_uniswap_factory_contract.functions.getPair(token_address, BASE_WETH_ADDRESS).call()
    return base_pair_address

#BSC

def get_pair_address_bsc(token_address):
    factory_contract = bsc_web3.eth.contract(address=PANCAKE_FACTORY_ADDRESS, abi=PANCAKESWAP_FACTORY_ABI)
    pair_address = factory_contract.functions.getPair(token_address, WBNB_ADDRESS).call()
    return pair_address
def get_token_bsc_details(token_address):
    token_contract = bsc_web3.eth.contract(address=token_address, abi=ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimals = token_contract.functions.decimals().call()
    return name, symbol, decimals

def get_weth_price_in_usd():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=weth&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data['weth']['usd']


def get_token_price(token_address,pair_address):
    chainlink_contract = web3.eth.contract(address=Web3.to_checksum_address(ETH_USD_ADDRESS), abi=ETH_USD_ABI)
    pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_PAIR_ABI)
    # Get the reserves from the pair contract
    reserves = pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]

    # Get the token addresses of the pair
    token0 = pair_contract.functions.token0().call()
    token1 = pair_contract.functions.token1().call()

    # Determine which reserve corresponds to the token and which to USDC
    if token0.lower() == token_address.lower():
        token_reserve = reserve0
        usdc_reserve = reserve1
    else:
        token_reserve = reserve1
        usdc_reserve = reserve0

    # Token price in USD
    token_price = usdc_reserve / token_reserve
    eth_usd_price = chainlink_contract.functions.latestAnswer().call() / 1e8  # Chainlink price feed returns price with 8 decimals

    # Adjust price to USD with correct decimal precision
    return token_price*eth_usd_price

BASE_CHAINLINK_PRICE_FEED_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [
            {"name": "", "type": "int256"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

BASE_CHAINLINK_PRICE_FEED_ADDRESS = '0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70'  # Replace with the actual address
THIS_BASE_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [
            {"name": "", "type": "address"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [
            {"name": "", "type": "address"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Replace with the actual Chainlink price feed contract ABI on Base
CHAINLINK_PRICE_FEED_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [
            {"name": "", "type": "int256"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]
# Create Chainlink price feed contract instance
base_chainlink_contract = base_web3.eth.contract(address=BASE_CHAINLINK_PRICE_FEED_ADDRESS, abi=BASE_CHAINLINK_PRICE_FEED_ABI)
def get_base_token_price(token_address, pair_address):
    try:
        base_rpc_url = 'https://mainnet.base.org'
        base_web3 = Web3(Web3.HTTPProvider(base_rpc_url))
        base_pair_contract = base_web3.eth.contract(address=pair_address, abi=THIS_BASE_PAIR_ABI)
        # Get the reserves from the pair contract
        base_reserves = base_pair_contract.functions.getReserves().call()
        base_reserve0 = base_reserves[0]
        base_reserve1 = base_reserves[1]
        # Get the token addresses of the pair
        base_token0 = base_pair_contract.functions.token0().call()
        base_token1 = base_pair_contract.functions.token1().call()

        # Determine which reserve corresponds to the token and which to the base token (similar to BNB on BSC)
        if base_token0.lower() == token_address.lower():
            base_token_reserve = base_reserve0
            base_base_token_reserve = base_reserve1
        else:
            base_token_reserve = base_reserve1
            base_base_token_reserve = base_reserve0

        # Token price in the base token
        base_token_price_in_base_token = base_base_token_reserve / base_token_reserve

        # Fetch the current base token price in USD from Chainlink
        base_base_token_usd_price = base_chainlink_contract.functions.latestAnswer().call() / 1e8  # Chainlink price feed returns price with 8 decimals

        # Token price in USD
        base_token_price_in_usd = base_token_price_in_base_token * base_base_token_usd_price

        return base_token_price_in_usd
    except Exception as e:
        return e


BSC_CONTRACT_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def get_wbnb_price_in_usd():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=wbnb&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data['wbnb']['usd']
PANCAKE_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

CHAINLINK_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [{"name": "", "type": "int256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

CHAINLINK_BNB_USD_ADDRESS = Web3.to_checksum_address('0x0567F2323251f0Aab15c8DfB1967E4e8A7D42aeE')

# Create Chainlink contract instance
bsc_chainlink_contract = bsc_web3.eth.contract(address=CHAINLINK_BNB_USD_ADDRESS, abi=CHAINLINK_ABI)



##base
BASE_PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    }
]


def handle_base_swap_event(event,decimal,name,symbol,base_addr,base_pair,chat_id):
    try:
        args = event['args']
        sender = args['sender']
        to = args['to']
        amount0_in = args['amount0In']
        amount1_in = args['amount1In']
        amount0_out = args['amount0Out']
        amount1_out = args['amount1Out']

        if (amount0_out > amount0_in) and (amount1_out <= amount1_in):
            contract = base_web3.eth.contract(address=base_addr, abi=BASE_CONTRACT_ABI)

            # Get total supply of the token
            total_supply = contract.functions.totalSupply().call()

            # Define the burn address (commonly used burn address)
            burn_address = '0x0000000000000000000000000000000000000000'

            # Get burned tokens (balance of the burn address)
            burned_tokens = contract.functions.balanceOf(burn_address).call()

            # Calculate circulating supply
            circulating_supply = total_supply - burned_tokens

            # Convert from wei (if needed, depending on token decimals, assuming 18 decimals here)
            total_supply_eth = Web3.from_wei(total_supply, 'ether')
            burned_tokens_eth = Web3.from_wei(burned_tokens, 'ether')
            circulating_supply_eth = Web3.from_wei(circulating_supply, 'ether')
            price = get_base_token_price(base_addr,base_pair)
            print(price)

            MKT_base = price *float(circulating_supply_eth)

            def format_market_cap(market_cap):
                if market_cap >= 1_000_000:
                    return f"{market_cap / 1_000_000:.2f}M"
                elif market_cap >= 1_000:
                    return f"{market_cap / 1_000:.2f}K"
                else:
                    return f"{market_cap:.2f}"
            formatted_market_cap = format_market_cap(MKT_base)

            usd_value_bought= float(price) * (float(amount0_out)*10**-18)
            dec = int(decimal)
            action = "Signal detected:"
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            chart_url=f"https://dexscreener.com/base/{base_pair}"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'
            number = amount1_in * 10**-18
            # ew_weth =f"{number:.20f}"
            emoji = get_emoji_from_db(chat_id)
            buy_step_number = retrieve_group_number(chat_id)
            gr = amount0_out * 10**-dec
            useage = format_with_unicode(gr)
            use_weth = format_with_unicode(number)
            if buy_step_number == None:
                buuy = 10
            else:
                buuy = buy_step_number
            calc = int(usd_value_bought/buuy)
            # print(type(usd_value_bought))
            if usd_value_bought <= 0.00:
                usd_value_bought = '<0.01'
            else:
                usd_value_bought = usd_value_bought

            if emoji:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{emoji*calc}\n"
                    f"💵 {use_weth} <b>WETH</b>\n"
                    f"🪙{useage} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"🧢MKT Cap : ${formatted_market_cap}\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
            
            else:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"🟢🟢🟢🟢🟢🟢🟢🟢🟢\n"
                    f"💵 {use_weth} <b>WETH</b>\n"
                    f"🪙{useage} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"🧢MKT Cap : ${formatted_market_cap}\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message

        else:
            pass

    except Exception as e:
        print(e)

async def base_log_loop(base_event_filter, poll_interval,context, chat_id,decimal,name,symbol,base_addr,base_pair):
    try:
        while True:
            for base_event in base_event_filter.get_new_entries():
                message=handle_base_swap_event(base_event,decimal,name,symbol,base_addr,base_pair,chat_id)
                if message:
                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id,file_type =media
                        if file_type =='photo':
                            await context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML')
                        elif file_type =='gif':
                            await context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML')
                    else:
                        print("No media found in the database for this group.")
                        await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                    # print(message)
            await asyncio.sleep(poll_interval)

    except Exception as e:
        print('base',e)

def base_start_logging(base_event_filter,poll_interval,context,chat_id,decimal,name,symbol,base_addr,base_pair):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()

    stop_event = stop_events[chat_id]
    stop_event.clear()
    asyncio.run_coroutine_threadsafe(
        base_log_loop(base_event_filter, poll_interval, context, chat_id,decimal,name,symbol,base_addr,base_pair),
        asyncio.get_event_loop()
    )

def bsc_get_token_price(token_address, pair_address):
    bsc_pair_contract = bsc_web3.eth.contract(address=pair_address, abi=PANCAKE_PAIR_ABI)

    # Get the reserves from the pair contract
    reserves = bsc_pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]

    # Get the token addresses of the pair
    token0 = bsc_pair_contract.functions.token0().call()
    token1 = bsc_pair_contract.functions.token1().call()

    # Determine which reserve corresponds to the token and which to BNB
    if token0.lower() == token_address.lower():
        token_reserve = reserve0
        bnb_reserve = reserve1
    else:
        token_reserve = reserve1
        bnb_reserve = reserve0

    # Token price in BNB
    token_price_in_bnb = bnb_reserve / token_reserve

    # Fetch the current BNB price in USD from Chainlink
    bnb_usd_price = bsc_chainlink_contract.functions.latestAnswer().call() / 1e8  # Chainlink price feed returns price with 8 decimals

    # Token price in USD
    token_price_in_usd = token_price_in_bnb * bnb_usd_price

    return token_price_in_usd

def handle_bsc_events(event,bsc_addr,bsc_pair,name,symbol,decimal,chat_id):
    try:
    # print(f"Swap event detected: {event}")
        args = event['args']
        sender = args['sender']
        to = args['to']
        amount0In = args['amount0In']
        amount1In = args['amount1In']
        amount0Out = args['amount0Out']
        amount1Out = args['amount1Out']
        
        if (amount0Out > amount0In) and (amount1Out <= amount1In):
            bsc_contract = bsc_web3.eth.contract(address=bsc_addr, abi=BSC_CONTRACT_ABI)
            # Get total supply of the token
            bsc_total_supply = bsc_contract.functions.totalSupply().call()

            # Define the burn address (commonly used burn address)
            burn_address = '0x0000000000000000000000000000000000000000'

            # Get burned tokens (balance of the burn address)
            burned_tokens = bsc_contract.functions.balanceOf(burn_address).call()

            # Calculate circulating supply
            bsc_circulating_supply = bsc_total_supply - burned_tokens

            # Convert from wei (if needed, depending on token decimals, assuming 18 decimals here)
            bsc_circulating_supply_eth = Web3.from_wei(bsc_circulating_supply, 'ether')
            curr_bsc_price =bsc_get_token_price(bsc_addr,bsc_pair)
            wbnb_price_usd = get_wbnb_price_in_usd()

            bsc_MKT_cap = curr_bsc_price * float(bsc_circulating_supply_eth)
            def bsc_format_market_cap(market_cap):
                if market_cap >= 1_000_000:
                    return f"{market_cap / 1_000_000:.2f}M"
                elif market_cap >= 1_000:
                    return f"{market_cap / 1_000:.2f}K"
                else:
                    return f"{market_cap:.2f}"
            bsc_formatted_market_cap = bsc_format_market_cap(bsc_MKT_cap)
            print(wbnb_price_usd)
            usd_value_bought = float((amount1In * 10**-18)) * wbnb_price_usd
            deci = int(decimal)

            action = "signal detected:"
            formatted_number = "{:,.0f}".format(round(amount0Out* 10**-deci,5))
            chart_url=f'https://dexscreener.com/bsc/{bsc_pair}'
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'
            emoji = get_emoji_from_db(chat_id)
            buy_step_number = retrieve_group_number(chat_id)
            if buy_step_number == None:
                buuy = 10
            else:
                buuy = buy_step_number
            calc = int(usd_value_bought/buuy)
            if emoji:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{emoji*calc}\n"
                    f"💵 {amount1In * 10**-18} <b>BSC</b>\n"
                    f"🪙{formatted_number} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"🧢MKT Cap : ${bsc_formatted_market_cap}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
            else:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{'🟢'*calc}\n"
                    f"💵 {amount0In * 10**-18} <b>BSC</b>\n"
                    f"🪙{formatted_number} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"🧢MKT Cap : ${bsc_formatted_market_cap}\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message


        else:
            pass 
    except Exception as e:
        print(e)

def handle_event(event,decimal,name,symbol,addr,pair,chat_id):
    try:
        # print(f"Swap event detected: {event}")
        args = event['args']
        sender = args['sender']
        to = args['to']
        amount0In = args['amount0In']
        amount1In = args['amount1In']
        amount0Out = args['amount0Out']
        amount1Out = args['amount1Out']
        # Determine if it's a buy
        if (amount0In < amount0Out) and (amount1In >= amount1Out):
            current_price_usd = get_token_price(addr,pair)
            weth_price_usd = get_weth_price_in_usd()
            contract = web3.eth.contract(address=addr, abi=CONTRACT_ABI)
            # Get total supply of the token
            total_supply = Web3.from_wei(contract.functions.totalSupply().call(),'ether')
            # Define the burn address (commonly used burn address)
            burn_address = '0x0000000000000000000000000000000000000000'
            # Get burned tokens (balance of the burn address)
            burned_tokens = contract.functions.balanceOf(burn_address).call()
            # Calculate circulating supply
            circulating_supply = total_supply - burned_tokens
            # Convert from wei (if needed, depending on token decimals, assuming 18 decimals here)
            circulating_supply_eth = Web3.from_wei(circulating_supply, 'ether')
            MKT_cap= float(circulating_supply) * current_price_usd

            def format_market_cap(market_cap):
                if market_cap >= 1_000_000:
                    return f"{market_cap / 1_000_000:.2f}M"
                elif market_cap >= 1_000:
                    return f"{market_cap / 1_000:.2f}K"
                else:
                    return f"{market_cap:.2f}"
            formatted_market_cap = format_market_cap(MKT_cap)
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            chart_url=f"https://dexscreener.com/ethereum/{pair}"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'


            print(int(decimal))
            dec=int(decimal)
            print(weth_price_usd)
            print(type(weth_price_usd))
            usd_value_bought = (float(amount1In)*10**-18) * weth_price_usd
            action = "Buy detected:"
            formatted_number = "{:,.0f}".format(round(amount0Out* 10**-dec,0))
            emoji = get_emoji_from_db(chat_id)
            buy_step_number = retrieve_group_number(chat_id)
            if buy_step_number == None:
                buuy = 10
            else:
                buuy = buy_step_number
            calc = int(usd_value_bought/buuy)
            if emoji:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{emoji*calc}\n"
                    f"💵 {round(amount1In * 10**-18,3)} <b>ETH</b>\n"
                    f"🪙{(formatted_number)} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"🧢MKT Cap : ${formatted_market_cap}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
            else:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{'🟢'*calc}\n"
                    f"💵 {round(amount1In * 10**-18,3)} <b>ETH</b>\n"
                    f"🪙{(formatted_number)} <b>{symbol}</b>\n"
                    f"🔷${usd_value_bought:.2f}\n"
                    f"MKT Cap : ${formatted_market_cap}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
        else:
            pass  # Not a buy event, so return None

    except Exception as e:
        print(e)

async def log_loop(event_filter, poll_interval, context, chat_id,decimal,name,symbol,addr,pair,stop_event):
    try:
        while not stop_event.is_set():
            for event in event_filter.get_new_entries():
                message = handle_event(event,decimal,name,symbol,addr,pair,chat_id)
                if message:
                    # await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id, file_type = media
                        if file_type == 'photo':
                            await context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML')
                        elif file_type == 'gif':
                            await context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML')
                    else:
                        print("No media found in the database for this group.")
                        await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)

                    # Only send messages if they indicate a buy event
                    # await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
            await asyncio.sleep(poll_interval)
    except Exception as e:
        print('here for sure: ',e)
        await asyncio.sleep(2)
        await log_loop(event_filter,poll_interval, context, chat_id,decimal,name,symbol,addr,pair)
        print('over again')

async def bsc_log_loop(swap_event_filter, poll_interval,context,chat_id,bsc_addr,bsc_pair,name,symbol,decimal,stop_event):
    try:
        while not stop_event.is_set():
            for bsc_event in swap_event_filter.get_new_entries():
                message = handle_bsc_events(bsc_event,bsc_addr,bsc_pair,name,symbol,decimal,chat_id)
                if message:
                    print(message)
                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id,file_type =media
                        if file_type =='photo':
                            await context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML')
                        elif file_type == 'gif':
                            await context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML')
                    else:
                        print("No media found in the database for this group.")
                        await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                # await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
            await asyncio.sleep(poll_interval)
    except Exception as e:
        print('bsc', e)

def get_transaction_info(signature,token_address,chat_id):
    try:
        name,symbol = get_token_info(token_address,META_DATA_PROGRAM)
        tx_signature = Signature.from_string(str(signature))
        tx_info = CLIENT.get_transaction(
            tx_signature, "jsonParsed", max_supported_transaction_version=0
        )
        data = tx_info.value.transaction.meta
    
        post_token_balance = [
            item
            for item in data.post_token_balances
            if str(item.owner) == str(RAYDIUM_AUTHORITY)
        ]
        pre_token_balance = [
            item
            for item in data.pre_token_balances
            if str(item.owner) == str(RAYDIUM_AUTHORITY)
        ]

        base_token_account_index = None
        quote_token_account_index = None

        account__index = None
        for index, item in enumerate(post_token_balance):
            if str(item.mint) == str(token_address):
                base_token_account_index = item.account_index
                account__index = index + 1

        quote_token_account_index = post_token_balance[account__index].account_index
        if base_token_account_index and quote_token_account_index:
            post_token_a = [
                item
                for item in post_token_balance
                if item.account_index == base_token_account_index
            ]
            post_token_b = [
                item
                for item in post_token_balance
                if item.account_index == quote_token_account_index
            ]
            pre_token_a = [
                item
                for item in pre_token_balance
                if item.account_index == base_token_account_index
            ]
            pre_token_b = [
                item
                for item in pre_token_balance
                if item.account_index == quote_token_account_index
            ]

            token_a_base = post_token_a[0]
            token_a_quote = post_token_b[0]
            token_b_base = pre_token_a[0]
            token_b_quote = pre_token_b[0]

            ORDER = None
            GOT = None
            SPENT = None
            _PRICE = None
            MSG = None

            liquidity = token_a_quote.ui_token_amount.ui_amount
            if (
                token_a_base.ui_token_amount.ui_amount
                > token_a_quote.ui_token_amount.ui_amount
            ):
                _PRICE = (
                    token_a_quote.ui_token_amount.ui_amount
                    / token_a_base.ui_token_amount.ui_amount
                )
            else:
                _PRICE = (
                    token_a_base.ui_token_amount.ui_amount
                    / token_a_quote.ui_token_amount.ui_amount
                )

            PRICE = "{:.8f}".format(_PRICE)
            if token_a_base.mint == token_b_base.mint:
                ORDER = (
                    "SELL"
                    if token_a_base.ui_token_amount.ui_amount
                    > token_b_base.ui_token_amount.ui_amount
                    else "BUY"
                )
            if ORDER == "BUY":
                SPENT = (
                    token_a_quote.ui_token_amount.ui_amount
                    - token_b_quote.ui_token_amount.ui_amount
                )
                GOT = (
                    token_b_base.ui_token_amount.ui_amount
                    - token_a_base.ui_token_amount.ui_amount
                )

            else:
                SPENT = (
                    token_b_quote.ui_token_amount.ui_amount
                    - token_a_quote.ui_token_amount.ui_amount
                )
                GOT = (
                    token_a_base.ui_token_amount.ui_amount
                    - token_b_base.ui_token_amount.ui_amount
                )

            
            price_usd = float(calculate_asset_value(PRICE))
            MCAP = get_token_supply(token_address) * price_usd
            POOL = calculate_asset_value(liquidity)
            spent_usd = calculate_asset_value(SPENT)
            chart =f"<a href='https://birdeye.so/token/{token_address}/{token_address}'>Chart</a> ⋙ ⋙ <a href='https://solscan.io/tx/{str(signature)}'>TXN</a>"
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            trend=f"<a href='{trend_url}'>Trending</a>"

            print(ORDER)
            emoji = get_emoji_from_db(chat_id)
            buy_step_number = retrieve_group_number(chat_id)
            if buy_step_number == None:
                buuy = 10
            else:
                buuy = buy_step_number
            calc = int(spent_usd/buuy)
            if ORDER == "BUY":
                if emoji:
                    MSG = (
                        f"<b> ✅{name}</b> Buy!\n\n"
                        f"{emoji*calc}\n"
                        f"💵 {format_number(SPENT)} <b>SOL</b>\n"
                        f"🪙  {format_number(GOT)} <b>{symbol}</b>\n"
                        f"🔷${format_number(spent_usd)}\n"
                        f"🧢MKT Cap : ${format_number(MCAP)}\n"
                        f"🦎{chart} 🔷{trend}"
                    )

                else:
                    MSG = (
                        f"<b> ✅{name}</b> Buy!\n\n"
                        f"{'🟢'*9}\n"
                        f"💵 {format_number(SPENT)} <b>SOL</b>\n"
                        f"🪙  {format_number(GOT)} <b>{symbol}</b>\n"
                        f"🔷${format_number(spent_usd)}\n"
                        f"🧢MKT Cap : ${format_number(MCAP)}\n"
                        f"🦎{chart} 🔷{trend}"
                    )
                # MSG = (
                #     f"<b>{name} Buy!</b>\n\n Spent: {format_number(SPENT)} SOL (${format_number(spent_usd)})\n↳ Got: {format_number(GOT)} {symbol}\n\nPrice: {PRICE} WSOL (${format_number(price_usd)})\n"
                #     f"💰 MarketCap: ${format_number(MCAP)}\n💧Liquidity: {format_number(liquidity)} WSOL (${format_number(POOL)})\n\n"
                #     f"<a href='https://raydium.io/swap/?inputCurrency=sol&outputCurrency={token_address}'>Buy</a> ⋙ <a href='https://birdeye.so/token/{token_address}/{token_address}'>Chart</a> ⋙ ⋙ <a href='https://solscan.io/tx/{str(signature)}'>TXN</a>"
                # )
            else:
                ff = (
                    f"<b>{name} Sell!</b>\nSold: {format_number(GOT)} {symbol}\n∴ For: {format_number(SPENT)} SOL (${format_number(spent_usd)})\n\nPrice: {PRICE} WSOL (${format_number(price_usd)})\n"
                    f"💰 MarketCap: ${format_number(MCAP)}\n💧Liquidity: {format_number(liquidity)} WSOL (${format_number(POOL)})\n\n"
                    f"<a href='https://raydium.io/swap/?inputCurrency=sol&outputCurrency={token_address}'>Buy</a> ⋙ <a href='https://birdeye.so/token/{token_address}/{token_address}'>Chart</a> ⋙ ⋙ <a href='https://solscan.io/tx/{str(signature)}'>TXN</a>"
                )
                # print(ff)
            return MSG
    except Exception as e:
        print('over here',e)

async def listen_to_buy_events(token_address: str,chat_id,context,stop_event):
    try:
        async with connect("wss://api.mainnet-beta.solana.com") as websocket:
            await websocket.logs_subscribe(
                RpcTransactionLogsFilterMentions(Pubkey.from_string(token_address)),
                commitment="finalized",
            )
            processed_signatures = set()
            while not stop_event.is_set():
                try:
                    data = await websocket.recv()
                    # print(data)
                    _result = data[0].result
                    # print(_result)
                    if hasattr(_result, "value"):
                        result = _result.value
                        log_signature, logs = result.signature, result.logs
                        # print(logs)
                        if log_signature not in processed_signatures:
                            
                            if any(
                                "Program log: Instruction: Route" in log for log in logs
                            ) and all("Error Message" not in _log for _log in logs):
                                print(log_signature)
                                # CLIENT = PingSolanaClient(settings.PRIVATE_RPC_CLIENT)
                                message = get_transaction_info(log_signature,token_address,chat_id)
                                try:
                                    if message:
                                        media = fetch_media_from_db(chat_id)
                                        if media:
                                            file_id, file_type = media
                                            if file_type == 'photo':
                                                await context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML')

                                            elif file_type == 'gif':
                                                await context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML')
                                        else:
                                            print("No media found in the database for this group.")
                                            await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                                        # print('here:',message)
                                        # await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                                except Exception as e:
                                    print('thise',e)
                            else:
                                '''logger.error(f"Possible Failed Swap: {log_signature}")'''
                    else:
                        print("Unexpected message format")  # Debugging statement
                
                except ConnectionClosedError:
                    print("Connection closed, reconnecting...")
                    await asyncio.sleep(20)
                    await listen_to_buy_events(token_address,chat_id,context)

                except KeyboardInterrupt:
                    print("Interrupted by user")
                    break
                except Exception as e:
                    print('deadly',e)
    except Exception as e:
        print('brutal',e)

def sol_start_logging(sol_address,chat_id,context):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()
    asyncio.run_coroutine_threadsafe(
        listen_to_buy_events(sol_address,chat_id,context,stop_event),
        asyncio.get_event_loop()
    )


def bsc_start_logging(swap_event_filter,poll_interval,context,chat_id,bsc_addr,bsc_pair,name,symbol,decimal):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()
    asyncio.run_coroutine_threadsafe(
        bsc_log_loop(swap_event_filter, poll_interval, context, chat_id,bsc_addr,bsc_pair,name,symbol,decimal,stop_event),
        asyncio.get_event_loop()
    )
def start_logging(event_filter, poll_interval, context, chat_id,decimal,name,symbol,addr,pair):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()
    asyncio.run_coroutine_threadsafe(
        log_loop(event_filter, poll_interval, context, chat_id,decimal,name,symbol,addr,pair,stop_event),
        asyncio.get_event_loop()
    )
# Define a handler for when the bot is added to a group
async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.my_chat_member.new_chat_member.status == 'member':
        chat_id = update.my_chat_member.chat.id
        group_name = update.my_chat_member.chat.title
        logger.info(f"Bot added to group '{group_name}' (Chat ID: {chat_id})")
        welcome_message = (
            f'''
🚀✨ Welcome to ESCOBAR! ✨🚀  
Excited to be part of this group and ready to help. Let's make great things happen together!
'''   
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_message)
        #then it automatically creates a new key on the database

async def bot_removed_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member_update = update.chat_member
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status
    user_id = chat_member_update.new_chat_member.user.id

    logger.debug(f"Chat member update: {chat_member_update}")
    logger.info(f"Old status: {old_status}, New status: {new_status}, User ID: {user_id}")
    print(new_status)

    if old_status == 'member' and new_status == 'left' and user_id == context.bot.id:
        chat_id = chat_member_update.chat.id
        group_name = chat_member_update.chat.title
        logger.info(f"Bot removed from group '{group_name}' (Chat ID: {chat_id})")
        print(f"Bot removed from group '{group_name}' (Chat ID: {chat_id})")
    else:
        logger.debug("The bot has not been removed from the group.")
        print('Nothing happened')

async def start(update:Update , context:ContextTypes.DEFAULT_TYPE):
    #check chat type
    chat_type:str = update.message.chat.type
    chat_id  = update.message.from_user.id
    if chat_type == 'private':
        welcome_message = (
    f"<b>🎉 Welcome to Escobar Bot!</b>\n\n"
    f"I'm here to help you manage your web3 activities effortlessly. Here’s what I can do:\n\n"
    f"🟢 <b>/start</b> - Start your journey with Escobar.\n"
    f"⚙️ <b>/settings</b> - Customize your experience and adjust your preferences.\n"
    f"❌ <b>/remove</b> - Remove a token with ease (confirmation required).\n"
    f"➕ <b>/add</b> - Add a new token to your list.\n"
)

        await context.bot.send_message(chat_id=chat_id, text=welcome_message, parse_mode='HTML',disable_web_page_preview=True)

    else:
        await update.message.reply_text('This command is used in a private chat')

async def is_user_admin(update:Update,context:ContextTypes.DEFAULT_TYPE):
    ## check if usser is admin
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

async def add(update:Update , context:ContextTypes.DEFAULT_TYPE):
    chat_type:str = update.message.chat.type
    print(chat_type)
    original_message_id = update.message.message_id 
    if chat_type =='group' or chat_type == 'supergroup':
        chat_id = update.effective_chat.id
        if not await is_user_admin(update , context):
            await update.message.reply_text("You're not authorized to use this bot")
        else:
            bot_chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if bot_chat_member.status == "administrator":
                text = f'''
<B>💼Escobar</b>
Choose a Chain ⛓️'''
                keyboard = [
                [InlineKeyboardButton("💎Ethereum (ETH)", callback_data='eth')],
                [InlineKeyboardButton("🌐Binance Smart Chain (BSC)", callback_data='bsc')],
                [InlineKeyboardButton("🔵Base Chain (Base)", callback_data='base')],
                [InlineKeyboardButton("💡Ton Chain (Ton)", callback_data='ton')],
                [InlineKeyboardButton("⚡Solana Chain (SOL)", callback_data='sol')],
            ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text=text, reply_markup=reply_markup,parse_mode='HTML')
                
            else:
                await update.message.reply_text("❗️Ineed administrator permission to proceed. Please make me an admin!")
    else:
        await update.message.reply_text("This Command is only accessible on the group")

async def add_query(update:Update , context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    original_message_id = query.message.message_id
    await query.answer()
    if query.data == "eth":
        await query.edit_message_text(text="➡[💎ETH] Token address?")
        context.user_data['state'] = FOR_ETH
    elif query.data == 'bsc':
        await query.edit_message_text(text="➡[🌐BSC] Token address?")
        context.user_data['state'] = FOR_BSC
    elif query.data == 'base':
        await query.edit_message_text(text="➡[🔵BASE] Token address?")
        context.user_data['state'] = FOR_BASE
    elif query.data == 'sol':
        await query.edit_message_text(text="➡[⚡SOL] Token address?")
        context.user_data['state'] = FOR_SOL
    elif query.data =='ton':
        await query.edit_message_text(text="➡[💡TON(📦DeDust)] Pair address?")
        context.user_data['state'] = FOR_TON

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in stop_events:
        stop_events[chat_id].set() 
        print('stopped')
    else:
        print('fuck')
    chat_type: str = update.message.chat.type
    if chat_type == 'group' or chat_type == 'supergroup':
        chat_id = update.effective_chat.id
        if not await is_user_admin(update, context):
            await update.message.reply_text("You're not authorized to use this bot")
        else:   
            bot_chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if bot_chat_member.status == "administrator":
                group_token = fetch_token_address(chat_id)
                # Ask for confirmation
                text = f"Are you sure you want to remove token : {group_token}?"
                keyboard = [
                    [InlineKeyboardButton("✅Yes", callback_data='confirm_remove')],
                    [InlineKeyboardButton("❌No", callback_data='cancel_remove')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text=text, reply_markup=reply_markup)
            else:
                await update.message.reply_text("❗️I need administrator permission to proceed. Please make me an admin!")
    else:
        await update.message.reply_text("This Command is only accessible in the group")

async def done_too(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    if query.data == 'confirm_remove':
        print(chat_id)
        chat_id_to_delete = chat_id
        delete_chat_id(chat_id_to_delete) # Replace with actual token name
        await query.edit_message_text(text="Token has been removed successfully.")

    elif query.data == 'cancel_remove':
        await query.edit_message_text(text="Token removal has been cancelled.")

    else:
        print('didnt get that')


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type: str = update.message.chat.type
    if chat_type == 'group' or chat_type == 'supergroup':

        btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
        btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

        row2= [btn2]
        row7= [btn7]
        row9= [btn9]
        reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


        await update.message.reply_text(
            '🛠 Settings Menu:',
            reply_markup=reply_markup_pair
        )
    else:
        await update.message.reply_text("This Command is only accessible in the group")
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    original_message_id = query.message.message_id

    await query.answer()
    if query.data == 'buybot_settings':
        buy_number = retrieve_group_number(chat_id)
        print(buy_number)
        if buy_number == None:
            buy_number_use = 10
        else:
            buy_number_use = buy_number
         
        emoji = get_emoji_from_db(chat_id)
        if emoji:
            emoji_use = emoji
        else:
            emoji_use = '🟢'

        btn1=InlineKeyboardButton("📊 Gif / Image: 🔴", callback_data='gif_video')
        btn2=InlineKeyboardButton(f"{emoji_use} Buy Emoji", callback_data='buy_emoji') 
        btn4=InlineKeyboardButton(f"💲 Buy Step: ${buy_number_use}", callback_data='buy_step') 
        btn7=InlineKeyboardButton("📈 Token Price: 🔴", callback_data='token_price')
        btn8=InlineKeyboardButton("📉 Market Cap: 🟢", callback_data='market_cap')
        btn9=InlineKeyboardButton("📉 Chart: DexScreener", callback_data='chart_dexscreener')
        btn11=InlineKeyboardButton("🔙 Back To Group Settings", callback_data='back_group_settings')

        text ='''
<b>💼Escobar</b>

⚙Settings'''
        row1=[btn1]
        row2=[btn2,btn4]
        row5=[btn7,btn8]
        row6=[btn9]
        row8=[btn11]
        reply_markup_pair = InlineKeyboardMarkup([row1,row2,row5,row6,row8])
        await context.bot.send_message(chat_id,text, reply_markup=reply_markup_pair,reply_to_message_id=original_message_id,parse_mode='HTML')

async def another_query(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['state'] = SEND_MEDIA
    if context.user_data['state'] == SEND_MEDIA:
        query = update.callback_query
        chat_id = query.message.chat_id
        original_message_id = query.message.message_id
        if query.data == 'gif_video':
            context.user_data['state'] = SEND_MEDIA
            print('you clicked gif_video')
            await query.edit_message_text(text="Send me a image/gif")

        elif query.data == 'buy_emoji':
            print('you cicked emoji')
            await query.edit_message_text(text="Please send emoji")
            context.user_data['awaiting_emoji'] = True
        elif query.data == 'buy_step':
            print('here')
            await query.edit_message_text(text="Send me a number for your buy step")
            # print(query.message)
            context.user_data['awaiting_number'] = True
    else:
        print('hANDLE DIFFERENTLY')

async def handle_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    chat_id = update.effective_chat.id
    print(chat_id)
    if user_data.get('awaiting_emoji'):
        emoji = update.message.text
        print(type(emoji))
        if emoji:
            save_emoji_to_db(emoji, chat_id)
            await update.message.reply_text(f'Emoji {emoji} saved to database.')
            user_data['awaiting_emoji'] = False
        else:
            await update.message.reply_text('Please send a valid emoji.')
    else:
        await update.message.reply_text('Send /setemoji to start the emoji process.')

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.animation or update.message.text.startswith("http"):
        message = update.message
        chat_id = update.effective_chat.id
        try:

            if context.user_data['state'] == SEND_MEDIA:
                if message.photo:
                    file_id = message.photo[-1].file_id  # Get the highest resolution photo
                    save_or_update_media_in_db(file_id, 'photo', chat_id)
                    await message.reply_text("Photo received and saved.")
                    context.user_data.clear()

                elif message.animation:
                    file_id = message.document.file_id
                    save_or_update_media_in_db(file_id, 'gif', chat_id)
                    await message.reply_text("GIF received and saved.")
                    context.user_data.clear()
                else:
                    print('gggggg')

            else:
                print('ghhhhh')
        except Exception as e:
            print('An error occured please type /settings to send media')
            await context.bot.send_message(chat_id=chat_id, text='An error occured please type /settings to send media',parse_mode='HTML',disable_web_page_preview=True)


    else:
        print('handles differently')




async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    message_text = update.message.text
    if context.user_data.get('awaiting_emoji'):
        emoji = update.message.text
        if emoji:
            save_emoji_to_db(emoji, update.effective_chat.id)
            await update.message.reply_text(f'Emoji {emoji} saved to database.')
            context.user_data['awaiting_emoji'] = False
        else:
            await update.message.reply_text('Please send a valid emoji.')

    elif context.user_data.get('awaiting_number'):
        try:
            buy_step_number = update.message.text
            print(buy_step_number)
            save_or_update_group_buy_number(chat_id,buy_step_number)
            await update.message.reply_text('Buy Step saved.')
            context.user_data['awaiting_number'] = False

        except Exception as e:
            await update.message.reply_text('Send a valid number')
            context.user_data['awaiting_number'] = False



    elif update.message.text and update.message.text.startswith("http"):
            print('i am here')
            file_url = update.message.text
            if file_url.endswith(".gif"):
                try:
                    gif_file = download_file(file_url)
                    response = await context.bot.send_document(chat_id=chat_id, document=gif_file)
                    file_id = response.document.file_id
                    save_or_update_media_in_db(file_id, 'gif', chat_id)
                    await update.message.reply_text("GIF received from the link and saved.")
                except Exception as e:
                    await update.message.reply_text(f"Failed to process the link: {e}")
            else:
                await update.message.reply_text("Please provide a valid GIF link.")
    else:

        if 'state' in context.user_data:
            if context.user_data['state'] == FOR_ETH:
                context.user_data['message'] = message_text
                if is_valid_ethereum_address(context.user_data['message']):
                    token_address =context.user_data['message']
                    # Get pair address
                    pair_address = get_pair_address(token_address)
                    try:
                        if pair_address == '0x0000000000000000000000000000000000000000':
                            print("No pair found for the given token")
                            await context.bot.send_message(chat_id=chat_id, text=f'No pair found for the given token type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            token_address =context.user_data['message']
                            print(f"Pair address for the given token and WETH: {pair_address}")
                            token_name, token_symbol ,token_decimal= get_token_details(token_address)
                        ### now store to database    #start polling
                            ghcall= check_group_exists(chat_id)
                            if  ghcall == 'good':
                                db_token = fetch_token_address(chat_id)
                                print('user already exist')
                                await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {db_token}',parse_mode='HTML',disable_web_page_preview=True)
                            else:
                                done=insert_user(chat_id, token_address)
                                db_token = fetch_token_address(chat_id)
                                respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{db_token}\n"
                                    f"✅NAME : {token_name}\n"
                                    f"🔣SYMBOL : {token_symbol}\n"
                                )
                                await context.bot.send_message(chat_id=chat_id, text=respnse,parse_mode='HTML',disable_web_page_preview=True)
                                btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                                btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
                                btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                                row2= [btn2]
                                row7= [btn7]
                                row9= [btn9]
                                reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


                                await update.message.reply_text(
                                    '🛠 Settings Menu:',
                                    reply_markup=reply_markup_pair
                                )
                                swapping_pair_address = get_pair_address(db_token)
                                print('this' ,swapping_pair_address)
                                pair_contract = web3.eth.contract(address=swapping_pair_address, abi=PAIR_ABI)
                                # Create a filter for the Swap event
                                swap_event_filter = pair_contract.events.Swap.create_filter(fromBlock='latest')
                                # Start monitoring the swap events
                                try:
                                    print('started')
                                    start_logging(swap_event_filter, 2, context, chat_id,token_decimal,token_name,token_symbol,token_address,pair_address)
                                except KeyboardInterrupt:
                                    print("Stopped monitoring swap events")
                    except Exception as e:
                        response ="No details found for token type /add to add a different token"
                        await update.message.reply_text(response)
                        context.user_data.clear()
                        print(e)
                else:
                    response = "This is not a valid Ethereum address type /add to add a different token"
                    await update.message.reply_text(response)
                context.user_data.clear()
            elif context.user_data['state'] == FOR_BSC:
                context.user_data['message'] = message_text 
                try:
                    bsc_token_address = Web3.to_checksum_address(context.user_data['message']) 
                    print(bsc_token_address)
                    bsc_pair_address = get_pair_address_bsc(bsc_token_address)
                    print(bsc_pair_address)
                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='Invalid Token address type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                try:

                    if bsc_pair_address == '0x0000000000000000000000000000000000000000':
                        response ="No pair exists for the given token address and WBNB."
                        print("No pair exists for the given token address type /add to add a different token")
                        await update.message.reply_text(response)

                    else:
                        bsc_token_address =context.user_data['message']
                        print(f"The pair address for the given token and WBNB is: {bsc_pair_address}")
                        bsc_token_name, bsc_token_symbol,bsc_token_decimal=get_token_bsc_details(bsc_token_address)
                        response = f'''
                            token_name : {bsc_token_name}
            token_symbol_bsc':{bsc_token_symbol}
            bsc_pair_address': {bsc_pair_address}
            decimal':{bsc_token_decimal}''' 
                        bsc_ghcall= check_group_exists(chat_id)
                        if  bsc_ghcall == 'good':
                            bsc_db_token = fetch_token_address(chat_id)
                            print('user already exist')
                            await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {bsc_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            bsc_done=insert_user(chat_id, bsc_token_address)
                            bsc_db_token = fetch_token_address(chat_id)
                            bsc_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{bsc_db_token}\n"
                                    f"✅NAME : {bsc_token_name}\n"
                                    f"🔣SYMBOL : {bsc_token_symbol}\n"
                                )
                            await context.bot.send_message(chat_id=chat_id, text=bsc_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                            row2= [btn2]
                            row7= [btn7]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )
                            swapping_bsc_pair_address = get_pair_address_bsc(bsc_db_token)
                            print(swapping_bsc_pair_address)
                            pair_bsc_contract = bsc_web3.eth.contract(address=swapping_bsc_pair_address, abi=BSC_PAIR_ABI)
            # Create a filter for the Swap event
                            swap_bsc_event_filter = pair_bsc_contract.events.Swap.create_filter(fromBlock='latest')
                            try:
                                print('bsc_started')
                                bsc_start_logging(swap_bsc_event_filter,2,context,chat_id,bsc_token_address,bsc_pair_address,bsc_token_name,bsc_token_symbol,bsc_token_decimal)
                                context.user_data.clear()
                            except KeyboardInterrupt:
                                print('stopped monitoring bsc')
                            except Exception as e:
                                print('for bsc',e)
                                context.user_data.clear()
                except Exception as e:
                    response ="an error occured"
                    print('for base again',e)
            
            elif context.user_data['state'] == FOR_BASE:
                context.user_data['message'] = message_text 
                try:
                    base_token_address = context.user_data['message']
                    base_pair_address = get_base_pair_address(base_token_address)
                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='Invalid Token address type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                try:

                    if base_pair_address == '0x0000000000000000000000000000000000000000':
                        print("No pair exists for the given token address and Base.")
                    else:
                        base_token_address =context.user_data['message']
                        print(f"The pair address for the given token and Base is: {base_pair_address}")
                        print('gotten hee')
                        base_name,base_symbol,base_decimal = get_base_token_details(base_token_address)
                        base_call= check_group_exists(chat_id)
                        if  base_call == 'good':
                            base_db_token = fetch_token_address(chat_id)
                            print('user already exist')
                            await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {base_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            base_done=insert_user(chat_id, base_token_address)
                            base_db_token = fetch_token_address(chat_id)
                            base_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{base_db_token}\n"
                                    f"✅NAME : {base_name}\n"
                                    f"🔣SYMBOL : {base_symbol}\n"
                                )
                            await context.bot.send_message(chat_id=chat_id, text=base_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                            row2= [btn2]
                            row7= [btn7]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )
                            swapping_base_pair_address = get_base_pair_address(base_db_token)
                            print('that',swapping_base_pair_address)
                            base_pair_contract = base_again_web3.eth.contract(address=swapping_base_pair_address, abi=BASE_PAIR_ABI)
                            base_swap_event_filter = base_pair_contract.events.Swap.create_filter(fromBlock='latest')
                            try:
                                print('BASE_started')
                                base_start_logging(base_swap_event_filter,2,context,chat_id,base_decimal,base_name,base_symbol,base_token_address,base_pair_address)
                                context.user_data.clear()
                            except KeyboardInterrupt:
                                print('stopped monitoring base')
                            except Exception as e:
                                print('for base',e)
                                context.user_data.clear()
                except Exception as e:
                    response ="an error occured"
                    print('for base again',e)
            elif context.user_data['state'] == FOR_SOL:
                context.user_data['message'] = message_text 
                try:
                    solana_address = context.user_data['message']
                    get_account_info(solana_address)
                    sol_call= check_group_exists(chat_id)
                    if  sol_call == 'good':
                        sol_db_token = fetch_token_address(chat_id)
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sol_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                    else:
                        sol_name,sol_symbol = get_token_info(solana_address,META_DATA_PROGRAM)
                        sol_done=insert_user(chat_id, solana_address)
                        sol_db_token = fetch_token_address(chat_id)
                        sol_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{sol_db_token}\n"
                                    f"✅NAME : {sol_name}\n"
                                    f"🔣SYMBOL : {sol_symbol}\n"
                                )
                        await context.bot.send_message(chat_id=chat_id, text=sol_respnse,parse_mode='HTML',disable_web_page_preview=True)
                        btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                        btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
                        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                        row2= [btn2]
                        row7= [btn7]
                        row9= [btn9]
                        reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


                        await update.message.reply_text(
                            '🛠 Settings Menu:',
                            reply_markup=reply_markup_pair
                        )
                        print('starting sol')
                        sol_start_logging(solana_address,chat_id,context)
                        context.user_data.clear()

                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='Invalid Token address',parse_mode='HTML',disable_web_page_preview=True)
                    print('for sol',e)
                    context.user_data.clear()


            elif context.user_data['state'] == FOR_TON:
                context.user_data['message'] = message_text
                try:
                    ton_pair_address = context.user_data['message']
                    url = f'https://api.dedust.io/v2/pools/{ton_pair_address}/trades'
                    valid_ = requests.get(url)
                    if valid_.status_code == 200 and valid_.json() !=[]:
                        ton_call  = check_group_exists(chat_id)
                        if ton_call == 'good':
                            ton_db_token= fetch_token_address(chat_id)
                            print('user exist TON')
                            await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {ton_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            pair,ton_name,ton_symbol,price_usd,mktcap,data,native = get_ton_details(ton_pair_address)
                            ton_done = insert_user(chat_id,ton_pair_address)
                            ton_db_token= fetch_token_address(chat_id)
                            ton_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{ton_db_token}\n"
                                    f"✅NAME : {ton_name}\n"
                                    f"🔣SYMBOL : {ton_symbol}\n"
                                )
                            await context.bot.send_message(chat_id=chat_id, text=ton_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn7= InlineKeyboardButton("🤖 Set Up Custom Buy-Bot", callback_data='custom_buybot')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                            row2= [btn2]
                            row7= [btn7]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row7,row9])


                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )
                            print('ton_started')
                            start_ton_logging(ton_db_token,context,chat_id)
                            context.user_data.clear()
                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    print('for ton',e)
                    context.user_data.clear()
            else:
                print('none')
            # await update.message.reply_text(response)
        # context.user_data.clear()
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token('7388590270:AAERF8VNpxPfj4a4EOjnIm5PD981FIBNEz8').build()
    #========= Handlers =============#

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler('remove', remove))
    app.add_handler(CommandHandler('settings', settings))
     # Register the chat member handler to detect when the bot is added to a group
    app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(bot_removed_from_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(add_query,pattern='^(eth|bsc|ton|base|sol)$'))
    app.add_handler(CallbackQueryHandler(done_too,pattern='^(confirm_remove|cancel_remove)$'))
    app.add_handler(CallbackQueryHandler(button,pattern='^(buybot_settings)$'))
    app.add_handler(CallbackQueryHandler(another_query,pattern='^(gif_video|buy_emoji|buy_step)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.ANIMATION, handle_media))


    

    app.run_polling()
if __name__ == '__main__':
    main()