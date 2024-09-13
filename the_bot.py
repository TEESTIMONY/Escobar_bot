#============= imports =======================#
import logging
from telegram import Chat, ChatMember, ChatMemberUpdated, Update,InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,ChatMemberHandler,CallbackQueryHandler,ConversationHandler,MessageHandler,filters
import re
from web3 import Web3
import requests
import time
import aiomysql
import threading
import asyncio
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
# from solana_stuff import pump_fun
from requests.exceptions import RequestException, Timeout, ConnectionError
import base58
import struct
import traceback
import io
from dotenv import load_dotenv
import os 
import json
from telegram.error import TimedOut
from requests.exceptions import ConnectTimeout
from decimal import Decimal, getcontext
from mysql.connector import pooling
CG = CoinGeckoAPI()
cg = CoinGeckoAPI()
from requests.exceptions import HTTPError
PASSWORD_ = 'Testimonyalade@2003'
TOKEN_KEY_= '7388590270:AAERF8VNpxPfj4a4EOjnIm5PD981FIBNEz8'
CLIENT = Client("https://api.mainnet-beta.solana.com")
RAYDIUM_POOL = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_AUTHORITY = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
META_DATA_PROGRAM = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
WRAPPED_SOL = "So11111111111111111111111111111111111111112"
SEND_MEDIA = 'SEND_MEDIA'
stop_events = {}

# ============== Database ============================#
# db_config = {
#     'user': 'root',
#     'password': PASSWORD_,
#     'host': 'localhost',
#     'database': 'Escobar_bot',
    
# }

db_config = {
    'user': 'root',
    'password': PASSWORD_,
    'host': '67.205.191.138',
    'database': 'Escobar',
}

connection_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                              pool_size=32,  # Adjust based on your needs
                                              **db_config)

def create_connection():
    return connection_pool.get_connection()
def create_tables():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Create `group_numbers` table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_numbers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id BIGINT NOT NULL,
                    number INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_group (group_id)
                )
            """)

            # Create `media` table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_id VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    chat_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_chat (chat_id)

                )
            """)

            # Create `emojis` table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emojis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    emoji VARCHAR(50) NOT NULL,
                    chat_id BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_chat (chat_id)
                    
                )
            """)

            # Create `chat_info` table with UNIQUE constraint on `chat_id`
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    token_address VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pair_address VARCHAR(255),
                    blockchain VARCHAR(50),
                    UNIQUE KEY unique_chat (chat_id)
                )
            """)

            # Create `solana_price` table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solana_price (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    price DECIMAL(18, 8) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("Tables created successfully or already exist.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

def download_file(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Failed to download file")

def save_or_update_group_buy_number(group_id, number):
    conn = create_connection()
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

def fetch_pair_address_and_blockchain_for_group(chat_id):
    try:
        # Connect to the database
        to_connect = create_connection()

        if to_connect.is_connected():
            print("Connected to the database")

            cursor = to_connect.cursor()

            # Define the SQL query to retrieve pair_address and blockchain for a specific chat_id
            select_query = "SELECT pair_address, blockchain FROM chat_info WHERE chat_id = %s"

            # Execute the query with the chat_id parameter
            cursor.execute(select_query, (chat_id,))

            # Fetch all rows from the result of the query
            results = cursor.fetchall()

            # Check if any results were found
            if results:
                # Process and print the results
                for row in results:
                    pair_address = row[0]
                    blockchain = row[1]
                    return pair_address,blockchain
            else:
                return None
    except Error as e:
        print(f"Error: {e}")
    finally:
        if to_connect.is_connected():
            cursor.close()
            to_connect.close()
            print("Database connection closed.")
def retrieve_group_number(group_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM group_numbers WHERE group_id = %s", (group_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def retrieve_solana_price_from_db():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT price, updated_at FROM solana_price
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                price, updated_at = result
                return {"price": price, "updated_at": updated_at}
            else:
                return None
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    else:
        return None

def get_emoji_from_db(chat_id: int) -> str:
    conn = create_connection()
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

def chat_id_exists(chat_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM chat_info WHERE chat_id = %s", (chat_id,))
            result = cursor.fetchone()
            return result is not None
        except Error as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

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

def save_solana_price_to_db(price):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Check if there's already a record in the table
            cursor.execute("SELECT COUNT(*) FROM solana_price")
            record_count = cursor.fetchone()[0]

            if record_count == 0:
                # If no record exists, insert a new one
                cursor.execute("""
                    INSERT INTO solana_price (price, updated_at)
                    VALUES (%s, NOW())
                """, (price,))
            else:
                # If a record exists, update the existing record
                cursor.execute("""
                    UPDATE solana_price
                    SET price = %s, updated_at = NOW()
                """, (price,))

            conn.commit()
        except Error as e:
            print(f"Error: {e}")
        finally:
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
        for_connect = create_connection()
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

def fetch_token_address(group_id):
    try:
        # Establish a database connection
        connection = create_connection()
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

def delete_chat_id(chat_id):
    try:
        # Establish the connection
        to_delete = create_connection()

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

def insert_user(telegram_id, given_address, pair_address, blockchain):
    try:
        # Connect to the database
        to_connect = create_connection()

        if to_connect.is_connected():
            print("Connected to the database")

            cursor = to_connect.cursor()

            # Define the SQL command to insert a record
            insert_query = """
            INSERT INTO chat_info (chat_id, token_address, pair_address, blockchain)
            VALUES (%s, %s, %s, %s);
            """

            # Execute the SQL command
            cursor.execute(insert_query, (telegram_id, given_address, pair_address, blockchain))

            # Commit the transaction
            to_connect.commit()
            print("User data inserted successfully.")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if to_connect.is_connected():
            cursor.close()
            to_connect.close()

def save_media_to_db(chat_id, media_type, media_content):
    try:
        for_save =create_connection()
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
    conn =create_connection()
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

# ================ CONNECTIONS ======================================#
infura_url = 'https://mainnet.infura.io/v3/9a7cbdec6fb8401b99acf17aac6ad0d3'
web3 = Web3(Web3.HTTPProvider(infura_url))

bsc_url = 'https://bsc-dataseed.binance.org/'
bsc_web3 = Web3(Web3.HTTPProvider(bsc_url))

base_rpc_url = 'https://mainnet.base.org'
base_web3 = Web3(Web3.HTTPProvider(base_rpc_url))

base_again_url = "https://base-mainnet.g.alchemy.com/v2/UfcBQ-1JALhYM8g88BESGng2WnnkHWnd"  # Update with the actual Base RPC URL
base_again_web3 = Web3(Web3.HTTPProvider(base_again_url))


#============== Check connections ====================================#
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
##= ========================== Utils ==============================###

UNISWAP_FACTORY_ADDRESS = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
PANCAKESWAP_FACTORY_ADDRESS = Web3.to_checksum_address('0xca143ce32fe78f1f7019d7d551a6402fc5350c73')


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


ETH_USD_ABI = '[{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}]'
PANCAKE_FACTORY_ADDRESS = Web3.to_checksum_address('0xca143ce32fe78f1f7019d7d551a6402fc5350c73')
# WBNB token address on BSC
WBNB_ADDRESS = Web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')
# WBNB address (checksum format)
ETH_USD_ADDRESS = Web3.to_checksum_address('0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419')
# WETH token address on Uniswap V2
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
CHAINLINK_BNB_USD_ADDRESS = Web3.to_checksum_address('0x0567F2323251f0Aab15c8DfB1967E4e8A7D42aeE')
BASE_CHAINLINK_PRICE_FEED_ADDRESS = '0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70'  # Replace with the actual address

CHOOSING,FOR_ETH,FOR_BSC,FOR_BASE,FOR_TON,FOR_PUMP,SEND_MEDIA,FOR_MOON,FOR_PINK,FOR_DEXES,PINK_LUNCH = range(11)
uniswap_factory_contract = web3.eth.contract(address=UNISWAP_FACTORY_ADDRESS, abi=UNISWAP_FACTORY_ABI)
bsc_chainlink_contract = bsc_web3.eth.contract(address=CHAINLINK_BNB_USD_ADDRESS, abi=CHAINLINK_ABI)
base_uniswap_factory_contract = base_web3.eth.contract(address=BASE_UNISWAP_FACTORY_ADDRESS, abi=BASE_UNISWAP_FACTORY_ABI)
base_chainlink_contract = base_web3.eth.contract(address=BASE_CHAINLINK_PRICE_FEED_ADDRESS, abi=BASE_CHAINLINK_PRICE_FEED_ABI)
# ============ FUNC =========================================#
def is_valid_ethereum_address(address: str)-> bool:
    return re.match(r'^0x[a-fA-F0-9]{40}$', address) is not None

def get_pair_address(token_address):
    pair_address = uniswap_factory_contract.functions.getPair(token_address, WETH_ADDRESS).call()
    return pair_address

def get_token_details(token_address):
    token_contract = web3.eth.contract(address=token_address, abi=ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimal= token_contract.functions.decimals().call()
    return name, symbol,decimal

def get_token_price(token_address,pair_address):
    chainlink_contract = web3.eth.contract(address=Web3.to_checksum_address(ETH_USD_ADDRESS), abi=ETH_USD_ABI)
    pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_PAIR_ABI)
    # Get the reserves from the pair contract
    reserves = pair_contract.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]
    token0 = pair_contract.functions.token0().call()
    token1 = pair_contract.functions.token1().call()
    if token0.lower() == token_address.lower():
        token_reserve = reserve0
        usdc_reserve = reserve1
    else:
        token_reserve = reserve1
        usdc_reserve = reserve0

    token_price = usdc_reserve / token_reserve
    eth_usd_price = chainlink_contract.functions.latestAnswer().call() / 1e8  
    return token_price*eth_usd_price

def get_weth_price_in_usd():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=weth&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data['weth']['usd']

def format_market_cap(market_cap):
    if market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f}M"
    elif market_cap >= 1_000:
        return f"{market_cap / 1_000:.2f}K"
    else:
        return f"{market_cap:.2f}"
    
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

def get_token_bsc_details(token_address):
    token_contract = bsc_web3.eth.contract(address=token_address, abi=ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimals = token_contract.functions.decimals().call()
    return name, symbol, decimals

def get_pair_address_bsc(token_address):
    factory_contract = bsc_web3.eth.contract(address=PANCAKE_FACTORY_ADDRESS, abi=PANCAKESWAP_FACTORY_ABI)
    pair_address = factory_contract.functions.getPair(token_address, WBNB_ADDRESS).call()
    return pair_address

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

def get_wbnb_price_in_usd():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=wbnb&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data['wbnb']['usd']

def bsc_format_market_cap(market_cap):
    if market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f}M"
    elif market_cap >= 1_000:
        return f"{market_cap / 1_000:.2f}K"
    else:
        return f"{market_cap:.2f}"

def get_base_pair_address(token_address):
    base_pair_address = base_uniswap_factory_contract.functions.getPair(token_address, BASE_WETH_ADDRESS).call()
    return base_pair_address

def get_base_token_details(token_address):
    token_contract = base_web3.eth.contract(address=token_address, abi=BASE_ERC_20_ABI)
    name = token_contract.functions.name().call()
    symbol = token_contract.functions.symbol().call()
    decimals = token_contract.functions.decimals().call()
    return name, symbol, decimals

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

def get_account_info(account):
    client = Client("https://api.mainnet-beta.solana.com")

    account_instance =client.get_account_info_json_parsed(
        Pubkey.from_string(str(account))
    )
    return account_instance.value.data

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

def get_token_info(mint,program_id):
        program_address = get_program_address(str(mint),program_id)
        account_info_instance =get_account_info(program_address)
        token_info = unpack_metadata_account(account_info_instance)
        token_name = token_info["name"]
        token_symbol= token_info["symbol"]

        return token_name , token_symbol

def fetch_solana_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return data['solana']['usd']


def update_solana_price():
    while True:
        price = fetch_solana_price()
        save_solana_price_to_db(price)
        time.sleep(120)  # Wait for 2 minutes

def start_price_updater_thread():
    thread = threading.Thread(target=update_solana_price)
    thread.daemon = True  # Daemonize thread to stop it when the main program exits
    thread.start()

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
# ============================ ACTIONS ===================================#

# ======================== ETH ===============================================#

def handle_event(event,decimal,name,symbol,addr,pair,chat_id):
    try:
        # print(f"Swap event detected: {event}")
        trans_hash = event['transactionHash']
        TXN = trans_hash.hex()
        # print(formatted_string)
        args = event['args']
        sender = args['sender']
        # print(args['event'])
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
            formatted_market_cap = format_market_cap(MKT_cap)
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            chart_url=f"https://dexscreener.com/ethereum/{pair}"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'
            thenew_signer = f"{to[:7]}...{to[-4:]}"
            sign =f"<a href='https://etherscan.io/address/{to}'>{thenew_signer}</a>" 
            txn = f"<a href='https://etherscan.io/tx/{TXN}'>TXN</a>"
            dec=int(decimal)
            print(dec)
            print(amount1In)
            print(amount0Out)
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
            print(usd_value_bought)
            if chat_id_exists(chat_id):
                if emoji:
                    message = (
                        f"<b> ✅{name}</b> Buy!\n\n"
                        f"{emoji*calc}\n"
                        f"💵 {special_format(amount1In* 10**-18)} <b>ETH</b>\n"
                        f"🪙{special_format(amount0Out* 10**-dec)} <b>{symbol}</b>\n"
                        f"👤{sign}|{txn}\n"
                        f"🔷${special_format(usd_value_bought)}\n"
                        f"🧢MKT Cap : ${special_format(MKT_cap)}\n\n"
                        f"🦎{chart} 🔷{trend}"
                    )
                    return message
                else:
                    message = (
                        f"<b> ✅{name}</b> Buy!\n\n"
                        f"{'🟢'*calc}\n"
                        f"💵 {special_format(amount1In * 10**-18)} <b>ETH</b>\n"
                        f"🪙{special_format(amount0Out* 10**-dec)} <b>{symbol}</b>\n"
                        f"👤{sign}|{txn}\n"
                        f"🔷${special_format(usd_value_bought)}\n"
                        f"🧢MKT Cap : ${special_format(MKT_cap)}\n\n"
                        f"🦎{chart} 🔷{trend}"
                    )
                    return message
    # except Exception as e:
    #     print('An error occured ',e)
    except IndexError:
        print('e')


async def log_loop(event_filter, poll_interval, context, chat_id,decimal,name,symbol,addr,pair,stop_event):
    try:
        while not stop_event.is_set():
            print('on')

            for event in event_filter.get_new_entries():
                message = handle_event(event,decimal,name,symbol,addr,pair,chat_id)
                try:
                    if message:
                        # print(message)
                        media = fetch_media_from_db(chat_id)
                        if media:
                            file_id, file_type = media
                            if file_type == 'photo':
                                asyncio.run_coroutine_threadsafe(
                                    context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                    asyncio.get_event_loop()
                                )
                            elif file_type == 'gif':
                                asyncio.run_coroutine_threadsafe(
                                    context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                    asyncio.get_event_loop()
                                )   
                        else:
                            print("No media found in the database for this group.")
                            asyncio.run_coroutine_threadsafe(
                                context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                asyncio.get_event_loop()
                            )
                except Exception as e:
                    print(e)
            await asyncio.sleep(poll_interval)
    except IndexError:
        pass
    # except Exception as e:
    #     print('here for sure: ',e)
    #     await asyncio.sleep(2)
    #     await log_loop(event_filter,poll_interval, context, chat_id,decimal,name,symbol,addr,pair)
    #     print('over again')
    except KeyError:
        print('restarting .......')
        await asyncio.sleep(2)
        await log_loop(event_filter,poll_interval, context, chat_id,decimal,name,symbol,addr,pair,stop_event)

def start_logging(event_filter, poll_interval, context, chat_id, decimal, name, symbol, addr, pair):
    # This function will be run in a separate thread
    def run_event_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stop_event = asyncio.Event()
        if chat_id not in stop_events:
            stop_events[chat_id] = stop_event
        stop_event.clear()

        loop.run_until_complete(
            log_loop(event_filter, poll_interval, context, chat_id, decimal, name, symbol, addr, pair, stop_event)
        )
        loop.close()

    # Start a new thread with the event loop
    logging_thread = threading.Thread(target=run_event_loop)
    logging_thread.start()

#==================================== BSC ===========================================#
def handle_bsc_events(event,bsc_addr,bsc_pair,name,symbol,decimal,chat_id):
    try:
    # print(f"Swap event detected: {event}")
        trans_hash = event['transactionHash']
        TXN = trans_hash.hex()
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
            print(curr_bsc_price)
            wbnb_price_usd = get_wbnb_price_in_usd()
            bsc_MKT_cap = float(curr_bsc_price) * float(bsc_circulating_supply_eth)
            bsc_formatted_market_cap = bsc_format_market_cap(bsc_MKT_cap)
            usd_value_bought = float((amount1In * 10**-18)) * wbnb_price_usd
            deci = int(decimal)
            action = "signal detected:"
            formatted_number = "{:,.0f}".format(round(amount0Out* 10**-deci,5))
            chart_url=f'https://dexscreener.com/bsc/{bsc_pair}'
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'
            thenew_signer = f"{to[:7]}...{to[-4:]}"
            sign =f"<a href='https://bscscan.com/address/{to}'>{thenew_signer}</a>" 
            txn = f"<a href='https://bscscan.com/tx/{TXN}'>TXN</a>"
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
                    f"💵 {special_format(amount1In * 10**-18)} <b>BSC</b>\n"
                    f"🪙{special_format(amount0Out* 10**-deci)} <b>{symbol}</b>\n"
                    f"👤{sign}|{txn}\n"
                    f"🔷${special_format(usd_value_bought)}\n"
                    f"🧢MKT Cap : ${special_format(bsc_MKT_cap)}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
            else:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{'🟢'*calc}\n"
                    f"💵 {special_format(amount1In * 10**-18)} <b>BSC</b>\n"
                    f"🪙{special_format(amount0Out* 10**-deci)} <b>{symbol}</b>\n"
                    f"👤{sign}|{txn}\n"
                    f"🔷${special_format(usd_value_bought)}\n"
                    f"🧢MKT Cap : ${special_format(bsc_MKT_cap)}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
    except Exception as e:
        print('error ',e)

async def bsc_log_loop(swap_event_filter, poll_interval,context,chat_id,bsc_addr,bsc_pair,name,symbol,decimal,stop_event):
    try:
        while not stop_event.is_set():
            print('cool')
            for bsc_event in swap_event_filter.get_new_entries():
                message = handle_bsc_events(bsc_event,bsc_addr,bsc_pair,name,symbol,decimal,chat_id)
                if message:
                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id,file_type =media
                        if file_type =='photo':
                            asyncio.run_coroutine_threadsafe(
                                context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                asyncio.get_event_loop()
                            )  
                        elif file_type == 'gif':
                            asyncio.run_coroutine_threadsafe(
                                context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                asyncio.get_event_loop()
                            ) 
                    else:
                        print("No media found in the database for this group.")
                        asyncio.run_coroutine_threadsafe(
                            context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                            asyncio.get_event_loop()
                            ) 
            await asyncio.sleep(poll_interval)
    except KeyboardInterrupt:
        print('interupted')
    except Exception as e:
        print('bsc', e)

def bsc_start_logging(swap_event_filter, poll_interval, context, chat_id, bsc_addr, bsc_pair, name, symbol, decimal):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()
    # Function to run the asyncio loop in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            bsc_log_loop(swap_event_filter, poll_interval, context, chat_id, bsc_addr, bsc_pair, name, symbol, decimal, stop_event)
        )
    # Start the thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()


#================================= Base =============================================#

def handle_base_swap_event(event,decimal,name,symbol,base_addr,base_pair,chat_id):
    try:
        trans_hash = event['transactionHash']
        TXN = trans_hash.hex()
        args = event['args']
        sender = args['sender']
        to = args['to']
        amount0_in = args['amount0In']
        amount1_in = args['amount1In']
        amount0_out = args['amount0Out']
        amount1_out = args['amount1Out']

        if (amount0_out < amount0_in) and (amount1_out >= amount1_in):
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
            MKT_base = price *float(circulating_supply_eth)
            usd_value_bought= float(price) * (float(amount1_out)/10**18)
            dec = int(decimal)
            action = "Signal detected:"
            trend_url=f"https://t.me/BSCTRENDING/5431871"
            chart_url=f"https://dexscreener.com/base/{base_pair}"
            trend=f"<a href='{trend_url}'>Trending</a>"
            chart=f'<a href="{chart_url}">Chart</a>'
            thenew_signer = f"{to[:7]}...{to[-4:]}"
            sign =f"<a href='https://basescan.org/address/{to}'>{thenew_signer}</a>" 
            txn = f"<a href='https://basescan.org/tx/{TXN}'>TXN</a>"
            emoji = get_emoji_from_db(chat_id)
            number = amount0_in * 10**-18
            # ew_weth =f"{number:.20f}"
            emoji = get_emoji_from_db(chat_id)
            buy_step_number = retrieve_group_number(chat_id)
            gr = amount1_out * 10**-dec
            useage = special_format(gr)
            use_weth = special_format(number)
            if buy_step_number == None:
                buuy = 10
            else:
                buuy = buy_step_number
            calc = int(usd_value_bought/buuy)
            if emoji:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{emoji*calc}\n"
                    f"💵 {use_weth} <b>WETH</b>\n"
                    f"🪙{useage} <b>{symbol}</b>\n"
                    f"👤{sign}|{txn}\n"
                    f"🔷${special_format(usd_value_bought)}\n"
                    f"🧢MKT Cap : ${special_format(MKT_base)}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
            else:
                message = (
                    f"<b> ✅{name}</b> Buy!\n\n"
                    f"{'🟢'*calc}\n"
                    f"💵 {use_weth} <b>WETH</b>\n"
                    f"🪙{useage} <b>{symbol}</b>\n"
                    f"👤{sign}|{txn}\n"
                    f"🔷${special_format(usd_value_bought)}\n"
                    f"🧢MKT Cap : ${special_format(MKT_base)}\n\n"
                    f"🦎{chart} 🔷{trend}"
                )
                return message
    except Exception as e:
        print(e)

async def base_log_loop(base_event_filter, poll_interval,context, chat_id,decimal,name,symbol,base_addr,base_pair,stop_event):
    try:
        while not stop_event.is_set():
            print('base')
            for base_event in base_event_filter.get_new_entries():
                message=handle_base_swap_event(base_event,decimal,name,symbol,base_addr,base_pair,chat_id)
                if message:
                    media = fetch_media_from_db(chat_id)
                    if media:
                        file_id,file_type =media
                        if file_type =='photo':
                            asyncio.run_coroutine_threadsafe(
                                context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                asyncio.get_event_loop()
                            ) 
                        elif file_type =='gif':
                            asyncio.run_coroutine_threadsafe(
                                context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                            asyncio.get_event_loop()
                            ) 
                    else:
                        print("No media found in the database for this group.")
                        asyncio.run_coroutine_threadsafe(
                            context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                        asyncio.get_event_loop()
                            ) 
                    # print(message)
            await asyncio.sleep(poll_interval)
    except Exception as e:
        print('base',e)

def base_start_logging(base_event_filter, poll_interval, context, chat_id, decimal, name, symbol, base_addr, base_pair):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()
    # Function to run the asyncio loop in a separate thread
    def this_run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            base_log_loop(base_event_filter, poll_interval, context, chat_id, decimal, name, symbol, base_addr, base_pair, stop_event)
        )
    # Start the thread
    thread_another = threading.Thread(target=this_run_in_thread)
    thread_another.start()

def get_token_supply_mc_cap(mint):
        _supply = CLIENT.get_token_supply(Pubkey.from_string(str(mint)))
        return _supply.value.ui_amount

def get_total_solana_supply(mint):
        _supply = CLIENT.get_token_supply(Pubkey.from_string(str(mint)))
        return _supply.value.ui_amount

# ================================= Pumpfun ========================================##

async def pumpfun(token_address, interval, context, chat_id,stop_event,name,symbol):
    try:
        prev_res = None
        while not stop_event.is_set():
            url = "https://api.mainnet-beta.solana.com"
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [
                        token_address,
                        {"limit": 1}
                    ]
                }
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                signature = response.json()['result'][0]['signature']

                if signature != prev_res:
                    payload2 = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [
                            signature,
                            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                        ]
                    }

                    try:
                        response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
                        res_data = response2.json()
                        messages = res_data['result']['meta']['logMessages']

                        if 'Program log: Instruction: Swap' in messages:
                            print("Detected a Swap transaction!")
                            thing = res_data['result']['meta']['innerInstructions']
                            for i in thing:
                                if i['index']==3:
                                    print(i['instructions'][1]['parsed']['info']['tokenAmount']['uiAmount'])
                                    print(i['instructions'][3]['parsed']['info']['tokenAmount']['uiAmount'])
                            with open('h.json','w')as file:
                                json.dump(res_data,file,indent=4)

                        elif "Program log: Instruction: Buy" in messages:
                            signer =  res_data['result']['transaction']['message']['accountKeys']
                            for items in signer:
                                if items['signer'] == True:
                                    the_signer = items['pubkey']
                            data = res_data['result']['meta']['innerInstructions'][0]['instructions'][:7]
                            actual_authority = []
                            token_amount = None
                            solana_amount = None

                            for instance in data:
                                try:
                                    info = instance["parsed"]["info"]
                                    authority = info.get("authority")
                                    if authority:
                                        actual_authority.append(authority)
                                    if 'authority' in info:
                                        token_amount = float(info['amount']) * 10**-6
                                except KeyError:
                                    continue

                            for i in data:
                                try:
                                    info = i["parsed"]["info"]
                                    if info['destination'] == actual_authority[-1]:
                                        solana_amount = info['lamports'] * 10**-9
                                except KeyError:
                                    continue
                            chart =f"<a href='https://pump.fun/{token_address}'>Chart</a>"
                            trend_url=f"https://t.me/BSCTRENDING/5431871"
                            trend=f"<a href='{trend_url}'>Trending</a>"
                            thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                            sign =f"<a href='https://solscan.io/account/{the_signer}'>{thenew_signer}</a>" 
                            txn = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                            if token_amount and solana_amount:
                                supply = get_token_supply_mc_cap(token_address)
                                mk= float(solana_amount/token_amount)*supply
                                Mkt_cap = mk*float(retrieve_solana_price_from_db()['price'])
                                print(solana_amount/token_amount)
                                emoji = get_emoji_from_db(chat_id)
                                usd_value_bought= solana_amount * float(retrieve_solana_price_from_db()['price'])
                                buy_step_number = retrieve_group_number(chat_id)
                                if buy_step_number == None:
                                    buuy = 10
                                else:
                                    buuy = buy_step_number
                                calc = int(usd_value_bought/buuy)
                                if chat_id_exists(chat_id):
                                    if emoji:
                                        message = (
                                            f"<b> ✅{name}</b> Buy!\n\n"
                                            f"{emoji*calc}\n"
                                            f"💵 {special_format(solana_amount)} <b>SOL</b>\n"
                                            f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                            f"👤{sign}|{txn}\n"
                                            f"🔷${special_format(usd_value_bought)}\n"
                                            f"🧢MKT Cap : ${special_format(Mkt_cap)}\n\n"
                                            f"🦎{chart} 🔷{trend}"
                                        )   
                                    else:
                                        message = (
                                            f"<b> ✅{name}</b> Buy!\n\n"
                                            f"{'🟢'*calc}\n"
                                            f"💵 {special_format(solana_amount)} <b>SOL</b>\n"
                                            f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                            f"👤{sign}|{txn}\n"
                                            f"🔷${special_format(usd_value_bought)}\n"
                                            f"🧢MKT Cap : ${special_format(Mkt_cap)}\n\n"  
                                            f"🦎{chart} 🔷{trend}"
                                        )
                                    try:
                                        if message:
                                            media = fetch_media_from_db(chat_id)
                                            if media:
                                                file_id, file_type = media
                                                if file_type == 'photo':
                                                    asyncio.run_coroutine_threadsafe(
                                                        context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                                    asyncio.get_event_loop()
                                                        )
                                                elif file_type == 'gif':
                                                    asyncio.run_coroutine_threadsafe(
                                                        context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                                        asyncio.get_event_loop()
                                                        )
                                            else:
                                                print("No media found in the database for this group.")
                                                asyncio.run_coroutine_threadsafe(
                                                    context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                                asyncio.get_event_loop()
                                                        )
                                            # print('here:',message)
                                            # await context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True)
                                    except Exception as e:
                                        print('thise',e)
                            

                        else:
                            # await context.bot.send_message(chat_id=chat_id, text="Detected a Sell or Failed transaction.")
                            print('Detected a Sell or Failed transaction.')
                    except IndexError:
                        print('sell')
                    prev_res = signature
                else:
                    print('No new transactions detected.')  # Optional: Remove or replace with logging if needed
            except (ConnectionError, Timeout) as e:
                print(f"Restartig ..... ")
                await asyncio.sleep(3)  # Brief pause before retrying
                await pumpfun(token_address, interval, context, chat_id,stop_event, name,symbol)
                print('continued')
            except KeyError:
                print('restarting ...../|')
                await asyncio.sleep(3)
                await pumpfun(token_address, interval, context, chat_id,stop_event,name,symbol)
                print('continued')

            except RequestException as e:
                print(f"Restartig .....n ")
                await asyncio.sleep(5)  # Brief pause before retrying
                await pumpfun(token_address, interval, context, chat_id,stop_event,name,symbol)
            except TimedOut as e:
                print(f"Restarting .....g ")
                await asyncio.sleep(5)  # Brief pause before retrying
                await pumpfun(token_address, interval, context, chat_id,stop_event,name,symbol)
            await asyncio.sleep(interval)
    except Exception as e:
        print('pump',e)
        print(f"Restarting .....g ")
        await asyncio.sleep(5)  # Brief pause before retrying
        await pumpfun(token_address, interval, context, chat_id,stop_event,name,symbol)
    # except IndexError:
    #     print('index')

def start_sol_monitoring(token_address, interval, context, chat_id, name, symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()

    # Function to run the asyncio loop in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            pumpfun(token_address, interval, context, chat_id, stop_event, name, symbol)
        )
    # Start the thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()


#==========================moonshot ===============================================#
async def moonshot(token_address, context, chat_id,name , symbol,stop_event):
    prev_signature = None
    while not stop_event.is_set():
        print('moonshot')
        url = "https://api.mainnet-beta.solana.com"

        try:
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
            
            if signature != prev_signature:
                payload2 = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        signature,
                        {
                            "encoding": "jsonParsed",
                            "maxSupportedTransactionVersion": 0
                        }
                    ]
                }

                try:
                    response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
                    data = response2.json()
                    messages = data['result']['meta']['logMessages']
                    parsed = data['result']['meta']['innerInstructions'][0]['instructions'][1:]

                    if 'Program log: Instruction: Swap' in messages:
                        new = data['result']['meta']['innerInstructions'][1]['instructions'][3:7]

                    elif "Program log: Instruction: Buy" in messages:
                        signer =  data['result']['transaction']['message']['accountKeys']
                        data = data['result']['meta']['innerInstructions'][0]['instructions'][:7]
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
                                        
                            except KeyError:
                                continue

                        for i in data:
                            info = i["parsed"]["info"]
                            try:
                                if info.get('destination') == actual_authority[-1]:
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
                            emoji = get_emoji_from_db(chat_id)
                            thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                            sign =f"<a href='https://solscan.io/account/{the_signer}'>{thenew_signer}</a>" 
                            txn = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                            buy_step_number = retrieve_group_number(chat_id)
                            if buy_step_number == None:
                                buuy = 10
                            else:
                                buuy = buy_step_number
                            calc = int(usd_value_bought/buuy)

                            if chat_id_exists(chat_id):
                                if emoji:
                                    message = (
                                        f"<b> ✅{name}</b> Buy!\n\n"
                                        f"{emoji*calc}\n"
                                        f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                        f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                        f"👤{sign}|{txn}\n"
                                        f"🔷${special_format(usd_value_bought)}\n"
                                        f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                        f"🦎{chart} 🔷{trend}"
                                    )
                                else:
                                    message = (
                                        f"<b> ✅{name}</b> Buy!\n\n"
                                        f"{'🟢'*calc}\n"
                                        f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                        f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                        f"👤{sign}|{txn}\n"
                                        f"🔷${special_format(usd_value_bought)}\n"
                                        f"MKT Cap : ${special_format(mkt_cap)}\n\n"
                                        f"🦎{chart} 🔷{trend}"
                                    )

                            try:
                                if message:
                                    media = fetch_media_from_db(chat_id)
                                    if media:
                                        file_id, file_type = media
                                        if file_type == 'photo':
                                            asyncio.run_coroutine_threadsafe(
                                                context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                            asyncio.get_event_loop()
                                                )
                                        elif file_type == 'gif':
                                            asyncio.run_coroutine_threadsafe(
                                                context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                            asyncio.get_event_loop()
                                                )
                                    else:
                                        print("No media found in the database for this group.")
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                        asyncio.get_event_loop()
                                                )
                            except Exception as e:
                                print('thise',e)
                    else:
                        print('I think it is a failed transaction or sell')

                except IndexError:
                    print('Sell transaction detected')
                prev_signature = signature
            else:
                print('No new transactions')

        except ConnectTimeout:
            print("Connection timed out, retrying...")
            await asyncio.sleep(5)  # Wait before retrying

        except KeyError:
            print('restarting .....')
            await asyncio.sleep(5)
            moonshot(token_address,context, chat_id,name , symbol,stop_event)
        except Exception as e:
            print(f"An error occurred: {e}")
        
        await asyncio.sleep(5)  # Adjust the interval as needed

def start_moonshot(token_address, context, chat_id, name, symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()

    # Function to run the asyncio loop in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            moonshot(token_address, context, chat_id, name, symbol, stop_event)
        )

    # Start the thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()


#=========================== pinksale ====================================#

async def pinky(token_address, context, chat_id,name,symbol,stop_event):
    previous_resp = None
    while not stop_event.is_set():
        try:
            print('pink')
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
        
            if previous_resp != signature:
                response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
                res_data = response2.json()
                messages = res_data['result']['meta']['logMessages']
                parsed = res_data['result']['meta']['innerInstructions'][0]['instructions'][1:]
                # print(messages)
                if 'Program log: Instruction: Swap' in messages:
                    # print('filtered only swap now')
                    new =res_data['result']['meta']['innerInstructions'][1]['instructions'][3:7]
                    # print(parsed[0]['parsed']['info']['tokenAmount'])
                    # print(parsed[1]['parsed']['info']['tokenAmount'])
                elif "Program log: Instruction: Buy" in messages:
                    signer =  res_data['result']['transaction']['message']['accountKeys']
                    data = res_data['result']['meta']['innerInstructions'][2]['instructions']
                    actual_authority = []
                    for instance in data:
                        try:
                            info = instance["parsed"]["info"]
                            authority = instance["parsed"]["info"]["authority"]
                            # print(f"Authority: {authority}")
                            actual_authority.append(authority)
                            # print(info)
                            if 'authority' in info:
                                token=float(info['amount'])*10**-6
                            else:
                                pass
                            decimal = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']
                            for items in signer:
                                if items['signer'] == True:
                                    the_signer = items['pubkey']
                        except KeyError:
                            continue
                    for i in data:
                        try:
                            info = i["parsed"]["info"]
                            if info['destination'] == actual_authority[-1]:
                                sol_amount =info['lamports']*10**-9
                            else:
                                pass
                        except KeyError:
                            continue
                    chart =f"<a href='https://www.pink.meme/solana/token/{token_address}'>Chart</a>"
                    trend_url=f"https://t.me/BSCTRENDING/5431871"
                    trend=f"<a href='{trend_url}'>Trending</a>"
                    thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                    sign =f"<a href='https://solscan.io/account/{the_signer}'>{thenew_signer}</a>" 
                    txn = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                    if token and sol_amount:
                        supply = get_token_supply_mc_cap(token_address)
                        print(supply)
                        mk= float(sol_amount/token)*supply
                        Mkt_cap = mk*float(retrieve_solana_price_from_db()['price'])
                        print(Mkt_cap)
                        emoji = get_emoji_from_db(chat_id)
                        buy_step_number = retrieve_group_number(chat_id)
                        usd_value_bought = sol_amount *float(retrieve_solana_price_from_db()['price'])
                        if buy_step_number == None:
                            buuy = 10
                        else:
                            buuy = buy_step_number
                        calc = int(usd_value_bought/buuy)

                        if chat_id_exists(chat_id):
                            if emoji:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{emoji*calc}\n"
                                    f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                    f"🪙{special_format(token)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(usd_value_bought)}\n"
                                    f"🧢MKT Cap : ${special_format(Mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )
                            else:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{'🟢'*calc}\n"
                                    f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                    f"🪙{special_format(token)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(usd_value_bought)}\n"
                                    f"🧢MKT Cap : ${special_format(Mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )
                        try:
                            if message:
                                media = fetch_media_from_db(chat_id)
                                if media:
                                    file_id, file_type = media
                                    if file_type == 'photo':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                        asyncio.get_event_loop()
                                            )
                                    elif file_type == 'gif':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                        asyncio.get_event_loop()
                                            )
                                else:
                                    print("No media found in the database for this group.")
                                    asyncio.run_coroutine_threadsafe(
                                        context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                    asyncio.get_event_loop()
                                            )
                        except Exception as e:
                            print(e)
                    # print(data)
                    
                else:
                    print('i think is a failed transaction or sell ')
            else:
                print('already there') 
            previous_resp = signature
            await asyncio.sleep(5)  # Adjust the interval as needed
        except IndexError:
                print('sell')
        except KeyError:
            print('restarting ..... ')
            await asyncio.sleep(5)  # Adjust the interval as needed
            pinky(token_address,context, chat_id,name,symbol,stop_event)
        except Exception as e:
            print(e)

def start_pinky(token_address, context, chat_id, name, symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()

    # Function to run the asyncio loop in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            pinky(token_address, context, chat_id, name, symbol, stop_event)
        )

    # Start the thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()

## =============================== pinksale Launch Pad ======================================#
async def pinksale_lunch(token_address,context,chat_id):
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
            with open('k.json','w')as file: 
                    json.dump(res_data,file,indent= 4)
            decimals = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']
            amount_in_symbol = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['amount']
            another_data = res_data['result']['meta']['innerInstructions'][0]['instructions']
            with open('k.json','w')as file:
                    json.dump(res_data,file,indent= 4)
            sol_deposit_list = []    
            auth= []
            bo=[]  
            for i in another_data:
                info = i.get("parsed", {}).get("info", {})
                amount = info.get('amount')
                amount_sol = info.get('lamports')
                if amount:
                     authority = info.get('authority')
                     auth.append(authority)
                     bought = float(amount)*10**-decimals
                     bo.append(bought)
                else:
                    bo.append(0)
                    auth.append('')
                    #  print(f'Amount: {bought} SYMBOL',f'>>> {authority}' )
                if amount_sol:
                     sol_deposit_list.append(float(amount_sol)*10**-decimals) # for the amount in token
            # print(f'Deposited in sol: {sol_deposit_list[-1]}')
            total_supply =res_data['result']['meta']['preTokenBalances'][0]['uiTokenAmount']['amount']
            total_supply = float(total_supply)*10**-decimals
            owner =res_data['result']['meta']['preTokenBalances'][0]['owner']
            # print(total_supply)
            # print(auth)
            # print(bo)
            # print(sol_deposit_list[-1])
            # print(owner)
            # print(unit_consumed)
            if total_supply and sol_symbol and sol_name and auth and bo[-1]!=0 and sol_deposit_list[-1] and owner and unit_consumed:
                decimals = res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']

                thenew_signer = f"{owner[:7]}...{owner[-4:]}"
                txn = f"<a href='https://solscan.io/account/{owner}'>{thenew_signer}</a>"
                hash = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                print('message')

                message = (
                            f"<b> ✅NAME: {sol_name}</b>\n\n"
                            f"<b> ✅SYMBOL: {sol_symbol}</b>\n\n"
                            f"<b> 🧮Compute Units Consumed: {unit_consumed}</b>\n\n"
                            f"<b> 🧮Decimal: {decimals}</b>\n\n"
                            f"<b> 👤{txn} | {hash}</b>\n\n"
                            f"<b> 💰{bo[-1]} {sol_symbol}</b>\n\n"
                            f"<b> 💰Deposited in SOL: {sol_deposit_list[-1]}</b>\n\n"
                            f"<b> 💰Amount Raised: ${float(sol_deposit_list[-1])*float(retrieve_solana_price_from_db()['price'])}</b>\n\n"
                        )
                await context.bot.send_message(chat_id=chat_id,parse_mode='HTML', disable_web_page_preview=True , text=message)
            else:
                print('thats whatsup')
                thenew_signer = f"{owner[:7]}...{owner[-4:]}"
                txn = f"<a href='https://solscan.io/account/{owner}'>{thenew_signer}</a>"
                hash = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                # for i in range(len(auth)):
                #     print(f'Amount: {bo[i]} SYMBOL',f'>>> {auth[i]}' )
                print('message')
                account_index =res_data['result']['meta']['postTokenBalances'][0]['accountIndex']
                if account_index == 1:
                    amount =res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['uiAmount']
                    decimals =res_data['result']['meta']['postTokenBalances'][0]['uiTokenAmount']['decimals']

                    message = (
                                f"<b> ✅NAME: {sol_name}</b>\n\n"
                                f"<b> ✅SYMBOL: {sol_symbol}</b>\n\n"
                                f"<b> 🧮Compute Units Consumed: {unit_consumed}</b>\n\n"
                                f"<b> 🧮Decimal: {decimals}</b>\n\n"
                                f"<b> 👤{txn} | {hash}</b>\n\n"
                                f"<b> 💰{amount} {sol_symbol}</b>\n\n"
                                f"<b> 💰Deposited in SOL: {sol_deposit_list[-1]}</b>\n\n"
                                f"<b> 💰Amount Raised: ${float(sol_deposit_list[-1])*float(retrieve_solana_price_from_db()['price'])}</b>\n\n"
                            )
                    await context.bot.send_message(chat_id=chat_id,parse_mode='HTML', disable_web_page_preview=True , text=message)
        except IndexError:
            try:
                another_data = res_data['result']['meta']['innerInstructions'][0]['instructions']
                thenew_signer = f"{owner[:7]}...{owner[-4:]}"
                txn = f"<a href='https://solscan.io/account/{owner}'>{thenew_signer}</a>"
                hash = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                print('here')
                for item in another_data:
                    info = item.get("parsed", {}).get("info", {})
                    amount = info.get('lamports')
                    if amount:
                        # return float(amount)*10**-decimals#*sol price will give you in usd
                        message = (
                            f"<b> ✅NAME: {sol_name}</b>\n\n"
                            f"<b> ✅SYMBOL: {sol_symbol}</b>\n\n"
                            f"<b> 🧮Compute Units Consumed: {unit_consumed}</b>\n\n"
                            f"<b> 👤{txn} | {hash}</b>\n\n"
                            f"<b> 💰{float(amount)*10**-decimals} {sol_symbol}</b>\n\n"
                            f"<b> 💰Deposited in SOL: {sol_deposit_list[-1]}</b>\n\n"
                            f"<b> 💰Amount Raised: ${float(sol_deposit_list[-1])*float(retrieve_solana_price_from_db()['price'])}</b>\n\n"
                    )
                    await context.bot.send_message(chat_id=chat_id,parse_mode='HTML', disable_web_page_preview=True , text=message)
            except IndexError:
                print('okay')
                action = 'Upcomming ..........'
                if action and unit_consumed:
                    # return action,unit_consumed
                    message = (
                        f"<b> ✅NAME: {sol_name}</b>\n"
                        f"<b> ✅SYMBOL: {sol_symbol}</b>\n"
                        f"<b> 🧮Compute Units Consumed: {unit_consumed}</b>\n"
                        f"<b> 🎬{action}</b>\n"
                        f"<b> 💰Deposited in SOL: {sol_deposit_list[-1]}</b>\n"
                        f"<b> 💰Amount Raised: ${float(sol_deposit_list[-1])*float(retrieve_solana_price_from_db()['price'])}</b>\n\n"   
                    )
                    await context.bot.send_message(chat_id=chat_id,parse_mode='HTML', disable_web_page_preview=True , text=message)
            # return total_supply,sol_name,sol_symbol,sol_deposit_list[-1],owner,auth,bo,unit_consumed
        except Exception as e:
            print(e)
               
def start_lunch(token_address,context,chat_id):
    # Function to run the asyncio loop in a separate thread
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            pinksale_lunch(token_address,context,chat_id)
        )

    # Start the thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()


# ================================== Dexes ======================================#

api_count = 0

class AxiosInstance:
    def __init__(self, base_url):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json'
        })
        self.base_url = base_url

    def get(self, endpoint):
        try:
            response = self.session.get(self.base_url + endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {self.base_url + endpoint}:\n", e)
            return False

# Create instances for each base URL
axios_instance = AxiosInstance("https://api.geckoterminal.com/api/v2/")
# axios_instance_ton_viewer = AxiosInstance("https://tonapi.io/v2/")
def api_limit_wait():
    time.sleep(1)  # Adjust the sleep time according to your API rate limits
def solana_get_token(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/solana/tokens/{address}/info")

def solana_get_token_pools(address, page="1"):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/solana/tokens/{address}/pools?page={page}")
def solana_get_last_pools_trades(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/solana/pools/{address}/trades")
async def dexes(pool_address,token_address, context, chat_id,name,symbol,stop_event):
    try:
        prev_resp =None
        while not stop_event.is_set():
            print('dex is live')
            last_trades = solana_get_last_pools_trades(pool_address)
            token_pools = solana_get_token_pools(token_address, page="1")
            if last_trades:
                swap_event = last_trades['data'][0]
                signature = swap_event['attributes']['tx_hash']
                swap_kind = swap_event['attributes']['kind']
                the_signer = swap_event['attributes']['tx_from_address']

                if prev_resp != signature:
                    if swap_kind !='sell':
                        chart =f"<a href='https://dexscreener.com/solana/{pool_address}'>Chart</a>"
                        trend_url=f"https://t.me/BSCTRENDING/5431871"
                        trend=f"<a href='{trend_url}'>Trending</a>"
                        thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                        sign =f"<a href='https://solscan.io/account/{the_signer}'>{thenew_signer}</a>" 
                        txn = f"<a href='https://solscan.io/tx/{signature}'>TXN</a>"
                        sol_amount = swap_event['attributes']['from_token_amount']
                        token_amount = swap_event['attributes']['to_token_amount']
                        usd_value_bought=float(swap_event['attributes']['volume_in_usd'])
                        print('buy!!')
                        mkt_cap = token_pools['data'][-1]['attributes']['market_cap_usd']
                        fdv = token_pools['data'][-1]['attributes']['fdv_usd']
                        print(mkt_cap)
                        print(fdv)
                        if mkt_cap == None:
                            mkt_cap = fdv
                        emoji = get_emoji_from_db(chat_id)
                        buy_step_number = retrieve_group_number(chat_id)
                        # print(swap_event)
                        if buy_step_number == None:
                            buuy = 10
                        else:
                            buuy = buy_step_number
                        calc = (usd_value_bought/buuy)
                        calc = int(calc)
                        if chat_id_exists(chat_id):
                            if emoji:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{emoji*calc}\n"
                                    f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                    f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(int(usd_value_bought))}\n"
                                    f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )
                            else:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{'🟢'*calc}\n"
                                    f"💵 {special_format(sol_amount)} <b>SOL</b>\n"
                                    f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(int(usd_value_bought))}\n"
                                    f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )
                        if message:
                            print('hereeeeeeeeeeeeeeeeee')
                            media = fetch_media_from_db(chat_id)
                            if media:
                                print(message)
                                file_id, file_type = media
                                if file_type == 'photo':
                                    print('this')

                                    asyncio.run_coroutine_threadsafe(
                                        context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                    asyncio.get_event_loop()
                                        )
                                elif file_type == 'gif':
                                    print('ghgh')
                                    asyncio.run_coroutine_threadsafe(
                                        context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                    asyncio.get_event_loop()
                                        )
                                else:
                                    print('idont know')
                            else:
                                print("No media found in the database for this group.")
                                asyncio.run_coroutine_threadsafe(
                                    context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                asyncio.get_event_loop()
                                        )
                    prev_resp = signature
            else:
                print("Failed to retrieve last pool trades.")   
            await asyncio.sleep(2)  # Adjust the interval as needed
    except Exception as e:
        print(e)

def start_dexes(pool_address,token_address,context, chat_id, name, symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()


    def run_dex_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            dexes(pool_address,token_address, context, chat_id, name, symbol, stop_event)
        )

    # Start the thread
    thread = threading.Thread(target=run_dex_in_thread)
    thread.start()


## ====================================== TON =========================================##
#============================== ==========================================#
api_count = 0

class AxiosInstance:
    def __init__(self, base_url):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json'
        })
        self.base_url = base_url

    def get(self, endpoint):
        try:
            response = self.session.get(self.base_url + endpoint)
            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            if response.status_code == 429:
                print(f"Too many requests: {http_err}")
                return 'doit'
            else:
                print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {self.base_url + endpoint}:\n", e)
            return False
# Create instances for each base URL
axios_instance = AxiosInstance("https://api.geckoterminal.com/api/v2/")
axios_instance_ton_viewer = AxiosInstance("https://tonapi.io/v2/")
def api_limit_wait():
    time.sleep(1)  # Adjust the sleep time according to your API rate limits
def get_token(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/ton/tokens/{address}/info")

def get_token_pools(address, page="1"):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/ton/tokens/{address}/pools?page={page}")
def get_last_pools_trades(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/ton/pools/{address}/trades")

async def ton(pool_address,token_address, context, chat_id,name,symbol,stop_event):
    try:
        list_sig = []
        prev_resp =None
        while not stop_event.is_set():
            last_trades = get_last_pools_trades(pool_address)
            token_pools = get_token_pools(token_address, page="1")
            if last_trades:
                swap_event = last_trades['data'][0] 
                signature = swap_event['attributes']['tx_hash']
                list_sig.append(signature)
                swap_kind = swap_event['attributes']['kind']
                the_signer = swap_event['attributes']['tx_from_address']
                if prev_resp != signature:
                    if swap_kind !='sell':
                        chart =f"<a href='https://dexscreener.com/ton/{pool_address}'>Chart</a>"
                        trend_url=f"https://t.me/BSCTRENDING/5431871"
                        trend=f"<a href='{trend_url}'>Trending</a>"
                        thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                        sign =f"<a href='https://tonviewer.com/{the_signer}'>{thenew_signer}</a>" 
                        txn = f"<a href='https://tonviewer.com/transaction/{signature}'>TXN</a>"
                        ton_amount = swap_event['attributes']['from_token_amount']
                        token_amount = swap_event['attributes']['to_token_amount']
                        usd_value_bought=float(swap_event['attributes']['volume_in_usd'])
                        print('buy!!')
                        mkt_cap = token_pools['data'][-1]['attributes']['market_cap_usd']
                        emoji = get_emoji_from_db(chat_id)
                        buy_step_number = retrieve_group_number(chat_id)
                        fdv = token_pools['data'][-1]['attributes']['fdv_usd']
                        # print(swap_event)
                        if mkt_cap == None:
                            mkt_cap = fdv
                        if buy_step_number == None:
                            buuy = 10
                        else:
                            buuy = buy_step_number
                        calc = (usd_value_bought/buuy)
                        calc = int(calc)

                        if chat_id_exists(chat_id):
                            if emoji:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{emoji*calc}\n"
                                    f"💵 {special_format(ton_amount)} <b>TON</b>\n"
                                    f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(usd_value_bought)}\n"
                                    f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )

                            else:
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{'🟢'*calc}\n"
                                    f"💵 {special_format(ton_amount)} <b>TON</b>\n"
                                    f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    f"👤{sign}|{txn}\n"
                                    f"🔷${special_format(usd_value_bought)}\n"
                                    f"🧢MKT Cap : ${special_format(mkt_cap)}\n\n"
                                    f"🦎{chart} 🔷{trend}"
                                )
                            # for i in list_sig:
                            #     if i!= prev_resp:
                            #         print(i)
                            #     prev_resp = i 
                            if message:
                                media = fetch_media_from_db(chat_id)
                                if media:
                                    file_id, file_type = media
                                    if file_type == 'photo':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_photo(chat_id=chat_id, photo=file_id,caption=message,parse_mode='HTML'),
                                        asyncio.get_event_loop()
                                            )
                                    elif file_type == 'gif':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_document(chat_id=chat_id, document=file_id,caption = message,parse_mode='HTML'),
                                        asyncio.get_event_loop()
                                            )
                                else:
                                    print("No media found in the database for this group.")
                                    asyncio.run_coroutine_threadsafe(
                                        context.bot.send_message(chat_id=chat_id, text=message,parse_mode='HTML',disable_web_page_preview=True),
                                    asyncio.get_event_loop()
                                            )
                    prev_resp = signature
            else:
                print("Failed to retrieve last pool trades.")   
            await asyncio.sleep(3)  # Adjust the interval as needed
    except Exception as e:
        print(e)

def start_ton(pool_address,token_address, context, chat_id,name,symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()


    def run_ton_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            ton(pool_address,token_address, context, chat_id,name,symbol,stop_event)
        )

    # Start the thread
    thread = threading.Thread(target=run_ton_in_thread)
    thread.start()


### ======================== Bot =============================#
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
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
                asyncio.run_coroutine_threadsafe(
                    update.message.reply_text(text=text, reply_markup=reply_markup,parse_mode='HTML'),
                asyncio.get_event_loop()
                    )
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
        keyboard = [
                [InlineKeyboardButton("🌊Dexes", callback_data='Dex')],
                [InlineKeyboardButton("🚀🎉PumpFun", callback_data='pumpfun')],
                [InlineKeyboardButton("🌕🚀Moonshot", callback_data='moonshot')],
                [InlineKeyboardButton("🎀💸PinkSale", callback_data='pinksale')],
                [InlineKeyboardButton("🎀💸Pinksale Lunchpad", callback_data='pinksale_lunch')],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text="➡[⚡SOL] Token address?",reply_markup=reply_markup)
        # context.user_data['state'] = FOR_SOL
    elif query.data =='ton':
        await query.edit_message_text(text="➡[💡TON] Token address?")
        context.user_data['state'] = FOR_TON

async def sol_query(update:Update,context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    original_message_id = query.message.message_id
    await query.answer()
    if query.data == 'pumpfun':
        print('pump')
        await query.edit_message_text(text="➡[🚀🎉PumpFun] Token address?")
        context.user_data['state'] = FOR_PUMP
    elif query.data == 'moonshot':
        await query.edit_message_text(text="➡[🌕🚀Moonshot] Token address?")
        context.user_data['state'] = FOR_MOON

    elif query.data == 'pinksale':
        await query.edit_message_text(text="➡[🎀💸PinkSale] Token address?")
        context.user_data['state'] = FOR_PINK
    elif query.data == 'Dex':
        await query.edit_message_text(text="➡[🌊Dexes] Token address?")
        context.user_data['state'] = FOR_DEXES
    elif query.data == 'pinksale_lunch':
        await query.edit_message_text(text="➡[🎀💸PinkSale Lunchpad] Token address?")
        context.user_data['state'] = PINK_LUNCH

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
                asyncio.run_coroutine_threadsafe(
                    update.message.reply_text(text=text, reply_markup=reply_markup),
                    asyncio.get_event_loop()
                            )
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
        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
        row2= [btn2]
        row9= [btn9]
        reply_markup_pair = InlineKeyboardMarkup([row2,row9])
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
        try:
            pair_adress,blockchain =fetch_pair_address_and_blockchain_for_group(chat_id)
        except Exception as e:
            blockchain = ''
            pair_adress= ''
        btn1=InlineKeyboardButton("📊 Gif / Image: 🔴", callback_data='gif_video')
        btn2=InlineKeyboardButton(f"{emoji_use} Buy Emoji", callback_data='buy_emoji') 
        btn4=InlineKeyboardButton(f"💲 Buy Step: ${buy_number_use}", callback_data='buy_step') 
        btn9=InlineKeyboardButton("📉 Chart: DexScreener", callback_data='chart_dexscreener',url=f'https://dexscreener.com/{blockchain}/{pair_adress}')
        btn11=InlineKeyboardButton("🔙 Back To Group Settings", callback_data='back_group_settings')

        text ='''
<b>💼Escobar</b>

⚙Settings'''
        row1=[btn1]
        row2=[btn2,btn4]
        row6=[btn9]
        row8=[btn11]
        reply_markup_pair = InlineKeyboardMarkup([row1,row2,row6,row8])
        await query.edit_message_text(text, reply_markup=reply_markup_pair,parse_mode='HTML')
    elif query.data == 'close_menu':
        await query.edit_message_reply_markup(reply_markup=None)

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
            context.user_data['awaiting_media'] = True
            await query.edit_message_text(text="Send me a image/gif")
        elif query.data == 'buy_emoji':
            print('you cicked emoji')
            await query.edit_message_text(text="Please send emoji")
            context.user_data['awaiting_emoji'] = True
        elif query.data == 'buy_step':
            print('here')
            await query.edit_message_text(text="Send me a number for your buy step")
            context.user_data['awaiting_number'] = True
        elif query.data == 'back_group_settings':
            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
            row2= [btn2]
            row9= [btn9]
            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
            await query.edit_message_reply_markup(reply_markup=reply_markup_pair)
async def handle_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    chat_id = update.effective_chat.id
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
        user_data = context.user_data
        if user_data.get('awaiting_media'):
            message = update.message
            chat_id = update.effective_chat.id
            try:
                if context.user_data['state'] == SEND_MEDIA:
                    if message.photo:
                        file_id = message.photo[-1].file_id
                        save_or_update_media_in_db(file_id, 'photo', chat_id)
                        await message.reply_text("Photo receivedgg and saved.")
                        context.user_data.clear()
                        user_data['awaiting_media'] = False
                    elif message.animation:
                        file_id = message.document.file_id
                        save_or_update_media_in_db(file_id, 'gif', chat_id)
                        await message.reply_text("GIF received and saved.")
                        context.user_data.clear()
                        user_data['awaiting_media'] = False
                    else:
                        context.user_data.clear()
                        user_data['awaiting_media'] = False
            except Exception as e:
               print('An error occured please type /settings to send media')

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
            if int(buy_step_number) < 10 :
                await update.message.reply_text('Buy Step should not be less than 10.')
            else:
                save_or_update_group_buy_number(chat_id,buy_step_number)
                await update.message.reply_text('Buy Step saved.')
                context.user_data['awaiting_number'] = False
        except Exception as e:
            print(e)
            await update.message.reply_text('An Error Occured please try again')
            context.user_data['awaiting_number'] = False
    elif update.message.text and update.message.text.startswith("http"):
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
                    print(pair_address)
                    block_chain = 'ethereum'
                    try:
                        if pair_address == '0x0000000000000000000000000000000000000000':
                            await context.bot.send_message(chat_id=chat_id, text=f'No pair found for the given token type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            token_address =context.user_data['message']
                            print(f"Pair address for the given token and WETH: {pair_address}")
                            token_name, token_symbol ,token_decimal= get_token_details(token_address)
                            ghcall= check_group_exists(chat_id)
                            if  ghcall == 'good':
                                db_token = fetch_token_address(chat_id)
                                print('user already exist')
                                await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {db_token}',parse_mode='HTML',disable_web_page_preview=True)
                            else:
                                done=insert_user(chat_id, token_address,pair_address,block_chain)
                                db_token = fetch_token_address(chat_id)
                                respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{token_address}\n"
                                    f"✅NAME : {token_name}\n"
                                    f"🔣SYMBOL : {token_symbol}\n"
                                )
                                await context.bot.send_message(chat_id=chat_id, text=respnse,parse_mode='HTML',disable_web_page_preview=True)
                                btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                                btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
                                row2= [btn2]
                                row9= [btn9]
                                reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                                await update.message.reply_text(
                                    '🛠 Settings Menu:',
                                    reply_markup=reply_markup_pair
                                )
                                pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)
                                swap_event_filter = pair_contract.events.Swap.create_filter(fromBlock='latest')
                                try:
                                    start_logging(swap_event_filter, 2, context, chat_id,token_decimal,token_name,token_symbol,token_address,pair_address)
                                    context.user_data.clear()
                                except KeyboardInterrupt:
                                    print("Stopped monitoring swap event")
                                    context.user_data.clear()
                    except Exception as e:
                        print('error ',e)
                        await context.bot.send_message(chat_id=chat_id, text='An Error Occured type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                        context.user_data.clear()

            elif context.user_data['state'] == FOR_BSC:
                context.user_data['message'] = message_text 
                try:
                    bsc_token_address = Web3.to_checksum_address(context.user_data['message']) 
                    bsc_pair_address = get_pair_address_bsc(bsc_token_address)
                    bsc_block_chain = 'bsc'
                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                try:
                    if bsc_pair_address == '0x0000000000000000000000000000000000000000':
                        response ="No pair exists for the given token address and WBNB."
                        print("No pair exists for the given token address type /add to add a different token")
                        await update.message.reply_text(response)
                    else:
                        bsc_token_address =context.user_data['message']
                        bsc_token_name, bsc_token_symbol,bsc_token_decimal=get_token_bsc_details(bsc_token_address)
                        bsc_ghcall= check_group_exists(chat_id)
                        if  bsc_ghcall == 'good':
                            bsc_db_token = fetch_token_address(chat_id)
                            await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {bsc_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            bsc_done=insert_user(chat_id, bsc_token_address,bsc_pair_address,bsc_block_chain)
                            bsc_db_token = fetch_token_address(chat_id)
                            bsc_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{bsc_token_address}\n"
                                    f"✅NAME : {bsc_token_name}\n"
                                    f"🔣SYMBOL : {bsc_token_symbol}\n"
                                )
                            await context.bot.send_message(chat_id=chat_id, text=bsc_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
                            row2= [btn2]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )
                            # swapping_bsc_pair_address = get_pair_address_bsc(bsc_db_token)
                            pair_bsc_contract = bsc_web3.eth.contract(address=bsc_pair_address, abi=BSC_PAIR_ABI)
                            swap_bsc_event_filter = pair_bsc_contract.events.Swap.create_filter(fromBlock='latest')
                            try:
                                bsc_start_logging(swap_bsc_event_filter,2,context,chat_id,bsc_token_address,bsc_pair_address,bsc_token_name,bsc_token_symbol,bsc_token_decimal)
                                context.user_data.clear()
                            except Exception as e:
                                print(e)
                                context.user_data.clear()
                except Exception as e:
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()
            elif context.user_data['state'] == FOR_BASE:
                context.user_data['message'] = message_text 
                try:
                    base_token_address = context.user_data['message']
                    base_pair_address = get_base_pair_address(base_token_address)
                    base_block_chain = 'base'
                except Exception as e:
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                try:

                    if base_pair_address == '0x0000000000000000000000000000000000000000':
                        print("No pair exists for the given token address and Base.")
                        await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                    else:
                        base_token_address =context.user_data['message']
                        print(f"The pair address for the given token and Base is: {base_pair_address}")
                        base_name,base_symbol,base_decimal = get_base_token_details(base_token_address)
                        base_call= check_group_exists(chat_id)
                        if  base_call == 'good':
                            base_db_token = fetch_token_address(chat_id)
                            await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {base_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            base_done=insert_user(chat_id, base_token_address,base_pair_address,base_block_chain)
                            # base_db_token = fetch_token_address(chat_id)
                            base_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{base_token_address}\n"
                                    f"✅NAME : {base_name}\n"
                                    f"🔣SYMBOL : {base_symbol}\n"
                                )
                            await context.bot.send_message(chat_id=chat_id, text=base_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
                            row2= [btn2]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )

                            base_pair_contract = base_again_web3.eth.contract(address=base_pair_address, abi=BASE_PAIR_ABI)
                            base_swap_event_filter = base_pair_contract.events.Swap.create_filter(fromBlock='latest')
                            try:
                                base_start_logging(base_swap_event_filter,2,context,chat_id,base_decimal,base_name,base_symbol,base_token_address,base_pair_address)
                                context.user_data.clear()
                            except KeyboardInterrupt:
                                print('stopped monitoring base')
                            except Exception as e:
                                print('for base',e)
                                context.user_data.clear()
                except Exception as e:
                        print('error ',e)
                        await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                        context.user_data.clear()

            elif context.user_data['state'] == FOR_PUMP:
                context.user_data['message'] = message_text 
                try:
                    solana_address = context.user_data['message']
                    print(solana_address)
                    get_account_info(solana_address)
                    sol_call= check_group_exists(chat_id)
                    if  sol_call == 'good':
                        sol_db_token = fetch_token_address(chat_id)
                        # sol_block_chain = 'solana'
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sol_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                    else:
                        sol_name,sol_symbol = get_token_info(solana_address,META_DATA_PROGRAM)
                        sol_done=insert_user(chat_id, solana_address,'','solana')
                        sol_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{solana_address}\n"
                                    f"✅NAME : {sol_name}\n"
                                    f"🔣SYMBOL : {sol_symbol}\n"
                                )
                        await context.bot.send_message(chat_id=chat_id, text=sol_respnse,parse_mode='HTML',disable_web_page_preview=True)
                        btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                        row2= [btn2]
                        row9= [btn9]
                        reply_markup_pair = InlineKeyboardMarkup([row2,row9])


                        await update.message.reply_text(
                            '🛠 Settings Menu:',
                            reply_markup=reply_markup_pair
                        )

                        start_sol_monitoring(solana_address,5,context,chat_id,sol_name,sol_symbol)
                        context.user_data.clear()
                except Exception as e:
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()

            elif context.user_data['state'] == FOR_MOON:
                context.user_data['message'] = message_text 
                try:
                    solana_address = context.user_data['message']
                    get_account_info(solana_address)
                    sol_call= check_group_exists(chat_id)
                    if  sol_call == 'good':
                        sol_db_token = fetch_token_address(chat_id)
                        # sol_block_chain = 'solana'
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sol_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                    else:
                        sol_name,sol_symbol = get_token_info(solana_address,META_DATA_PROGRAM)
                        sol_done=insert_user(chat_id, solana_address,'','solana')
                        sol_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{solana_address}\n"
                                    f"✅NAME : {sol_name}\n"
                                    f"🔣SYMBOL : {sol_symbol}\n"
                                )
                        await context.bot.send_message(chat_id=chat_id, text=sol_respnse,parse_mode='HTML',disable_web_page_preview=True)
                        btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')
                        row2= [btn2]
                        row9= [btn9]
                        reply_markup_pair = InlineKeyboardMarkup([row2,row9])


                        await update.message.reply_text(
                            '🛠 Settings Menu:',
                            reply_markup=reply_markup_pair
                        )
                    
                        start_moonshot(solana_address,context,chat_id,sol_name,sol_symbol)
                        context.user_data.clear()
                except Exception as e:
                    # await context.bot.send_message(chat_id=chat_id, text='Invalid Token address',parse_mode='HTML',disable_web_page_preview=True)
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()

            elif context.user_data['state'] == FOR_PINK:
                context.user_data['message'] = message_text 
                try:
                    solana_address = context.user_data['message']
                    print(solana_address)
                    get_account_info(solana_address)
                    sol_call= check_group_exists(chat_id)
                    if  sol_call == 'good':
                        sol_db_token = fetch_token_address(chat_id)
                        # sol_block_chain = 'solana'
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sol_db_token}',parse_mode='HTML',disable_web_page_preview=True)
                    else:
                        sol_name,sol_symbol = get_token_info(solana_address,META_DATA_PROGRAM)
                        sol_done=insert_user(chat_id, solana_address,'','solana')
                        # sol_db_token = fetch_token_address(chat_id)
                        sol_respnse = (
                                    f"🎯 Escobar is now tracking\n"
                                    f"📈{solana_address}\n"
                                    f"✅NAME : {sol_name}\n"
                                    f"🔣SYMBOL : {sol_symbol}\n"
                                )
                        await context.bot.send_message(chat_id=chat_id, text=sol_respnse,parse_mode='HTML',disable_web_page_preview=True)
                        btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                        btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                        row2= [btn2]
                        row9= [btn9]
                        reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                        await update.message.reply_text(
                            '🛠 Settings Menu:',
                            reply_markup=reply_markup_pair
                        )
                        start_pinky(solana_address,context,chat_id,sol_name,sol_symbol)
                        context.user_data.clear()
                except Exception as e:
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()
            
            elif context.user_data['state'] == PINK_LUNCH:
                context.user_data['message'] = message_text 
                try:
                    solana_address = context.user_data['message']
                    start_lunch(solana_address,context,chat_id)
                        # start_sol_monitoring(solana_address,5,context,chat_id,sol_name,sol_symbol)
                        # context.user_data.clear()
                except Exception as e:
                    print(e)

            elif context.user_data['state'] == FOR_DEXES:
                context.user_data['message'] = message_text 
                try:
                    sol_address = context.user_data['message']
                    token_info = solana_get_token(sol_address)
                    sol_check= check_group_exists(chat_id)
                    if  sol_check == 'good':
                        sol_db_token = fetch_token_address(chat_id)
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sol_db_token}',parse_mode='HTML',disable_web_page_preview=True)

                    else:
                        deep_down = token_info['data']['attributes']
                        if deep_down:
                            name = deep_down['name']
                            symbol = deep_down['symbol']
                            decimal = deep_down['decimals']
                            sol_done=insert_user(chat_id, sol_address,'','ton')
                            # sol_db_token = fetch_token_address(chat_id)
                            sol_respnse = (
                                        f"🎯 Escobar is now tracking\n"
                                        f"📈{sol_address}\n"
                                        f"✅NAME : {name}\n"
                                        f"🔣SYMBOL : {symbol}\n"
                                    )
                            await context.bot.send_message(chat_id=chat_id, text=sol_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                            row2= [btn2]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )

                            token_pools = solana_get_token_pools(sol_address, page="1")
                            if token_pools:
                                # print("Token Pools:", token_pools)
                                pair_address = token_pools['data'][0]['attributes']['address']
                                print(pair_address)

                                start_dexes(pair_address,sol_address,context,chat_id,name,symbol)
                                context.user_data.clear()

                            
                            else:
                                print("Failed to retrieve token pools.")
                                context.user_data.clear()
                except Exception as e:
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()

            elif context.user_data['state'] == FOR_TON:
                context.user_data['message'] = message_text 
                try:
                    ton_address = context.user_data['message']
                    token_info = get_token(ton_address)
                    ton_check= check_group_exists(chat_id)
                    if  ton_check == 'good':
                        ton_db_token = fetch_token_address(chat_id)
                        print('user already exist')
                        await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {ton_db_token}',parse_mode='HTML',disable_web_page_preview=True)

                    else:
                        deep_down = token_info['data']['attributes']
                        if deep_down:
                            name = deep_down['name']
                            symbol = deep_down['symbol']
                            decimal = deep_down['decimals']
                            ton_done=insert_user(chat_id, ton_address,'','ton')
                            # sol_db_token = fetch_token_address(chat_id)
                            ton_respnse = (
                                        f"🎯 Escobar is now tracking\n"
                                        f"📈{ton_address}\n"
                                        f"✅NAME : {name}\n"
                                        f"🔣SYMBOL : {symbol}\n"
                                    )
                            await context.bot.send_message(chat_id=chat_id, text=ton_respnse,parse_mode='HTML',disable_web_page_preview=True)
                            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
                            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

                            row2= [btn2]
                            row9= [btn9]
                            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
                            await update.message.reply_text(
                                '🛠 Settings Menu:',
                                reply_markup=reply_markup_pair
                            )

                            token_pools = get_token_pools(ton_address, page="1")
                            if token_pools:
                                # print("Token Pools:", token_pools)
                                pair_address = token_pools['data'][0]['attributes']['address']
                                print(pair_address)

                                start_ton(pair_address,ton_address, context, chat_id,name,symbol)
                                context.user_data.clear()

                            
                            else:
                                print("Failed to retrieve token pools.")
                                context.user_data.clear()

                        else:
                            await context.bot.send_message(chat_id=chat_id, text='Failed to retrieve token information.',parse_mode='HTML',disable_web_page_preview=True)
                except Exception as e:
                    print(e)
                    await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
                    context.user_data.clear()      
def main():
    create_tables()
    start_price_updater_thread()
    app = ApplicationBuilder().token(TOKEN_KEY_).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler('remove', remove))
    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(bot_removed_from_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(add_query,pattern='^(eth|bsc|ton|base|sol)$'))
    app.add_handler(CallbackQueryHandler(done_too,pattern='^(confirm_remove|cancel_remove)$'))
    app.add_handler(CallbackQueryHandler(button,pattern='^(buybot_settings|close_menu)$'))
    app.add_handler(CallbackQueryHandler(another_query,pattern='^(gif_video|buy_emoji|buy_step|back_group_settings)$'))
    app.add_handler(CallbackQueryHandler(sol_query,pattern='^(pumpfun|moonshot|pinksale|Dex|pinksale_lunch)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.ANIMATION, handle_media))
    app.run_polling()

if __name__ == '__main__':
    main()