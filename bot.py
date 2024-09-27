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


TOKEN_KEY_= '7253724097:AAFryLXOoAXEQbgFMyUFhe9VGUap9ZTQoAA'
CHOOSING,FOR_SUI =range(2)
PASSWORD_ = 'Testimonyalade@2003'
stop_events = {}
SEND_MEDIA = 'SEND_MEDIA'


# ======================= Db =================================================#
db_config = {
    'user': 'root',
    'password': PASSWORD_,
    'host': 'localhost',
    'database': 'telegram_bot',
    
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

def fetch_media_from_db(chat_id: int):
    conn =create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, file_type FROM media WHERE chat_id = %s ORDER BY created_at DESC LIMIT 1", (chat_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

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

def retrieve_group_number(group_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM group_numbers WHERE group_id = %s", (group_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

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

def download_file(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Failed to download file")

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

#========================== UTILS ============================================#
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
api_count = 0

# Helper function to handle API limit wait
def api_limit_wait():
    time.sleep(1)  # Adjust the sleep time according to your API rate limits

# Create an Axios-like instance using requests.Session with predefined headers
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

# Function to get token information by address
def get_token(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/sui-network/pools/{address}/info")
def get_token_pools(address, page="1"):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/sui-network/pools/{address}")

def get_last_pools_trades(address):
    global api_count
    api_count += 1
    api_limit_wait()
    return axios_instance.get(f"networks/sui-network/pools/{address}/trades")

# Set the API limit
api_limit = 29


async def suii(pool_address,context, chat_id,name,symbol,stop_event):
    try:
        prev_resp =None
        while not stop_event.is_set():
            print('sui is live')
            last_trades = get_last_pools_trades(pool_address)
            token_pools = get_token_pools(pool_address, page="1")
            if last_trades:
                swap_event = last_trades['data'][0]
                signature = swap_event['attributes']['tx_hash']
                swap_kind = swap_event['attributes']['kind']
                the_signer = swap_event['attributes']['tx_from_address']
                if prev_resp != signature:
                    if swap_kind !='sell':
                        chart =f"<a href='https://dexscreener.com/sui{pool_address}'>Chart</a>"
                        trend_url=f"https://t.me/BSCTRENDING/5431871"
                        trend=f"<a href='{trend_url}'>Trending</a>"
                        thenew_signer = f"{the_signer[:7]}...{the_signer[-4:]}"
                        sign =f"<a href='https://suiscan.xyz/mainnet/account/{the_signer}'>{thenew_signer}</a>" 
                        txn = f"<a href='https://suiscan.xyz/mainnet/tx/{signature}'>TXN</a>"
                        sol_amount = swap_event['attributes']['from_token_amount']
                        token_amount = swap_event['attributes']['to_token_amount']
                        usd_value_bought=float(swap_event['attributes']['volume_in_usd'])
                        print('buy!!')
                        mkt_cap = token_pools['data']['attributes']['market_cap_usd']
                        fdv = token_pools['data']['attributes']['fdv_usd']
                        print(mkt_cap)
                        print(fdv)
                        print(sol_amount)
                        print(token_amount)
                        print(usd_value_bought)
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

def start_suii(pool_address,context, chat_id, name, symbol):
    if chat_id not in stop_events:
        stop_events[chat_id] = asyncio.Event()
    stop_event = stop_events[chat_id]
    stop_event.clear()


    def run_sui_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            suii(pool_address,context, chat_id, name, symbol, stop_event)
        )

    # Start the thread
    thread = threading.Thread(target=run_sui_in_thread)
    thread.start()

# =================================== BOT ====================================#
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
🚀✨ Welcome to Sui Buybot! ✨🚀  
Excited to be part of this group and ready to help. Let's make great things happen together!
'''   
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_message)
        #then it automatically creates a new key on the database
        
async def start(update:Update , context:ContextTypes.DEFAULT_TYPE):
    #check chat type
    chat_type:str = update.message.chat.type
    chat_id  = update.message.from_user.id
    if chat_type == 'private':
        welcome_message = (
    f"<b>🎉 Welcome to Sui Buybot!</b>\n\n"
    f"I'm here to help you manage your web3 activities effortlessly. Here’s what I can do:\n\n"
    f"🟢 <b>/start</b> - Start your journey with Sui Buyboy.\n"
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
<B>Sui Buybot</b>
Choose a Chain ⛓️'''
                keyboard = [
                [InlineKeyboardButton("💧SUI", callback_data='sui')],
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
    if query.data == "sui":
        await query.edit_message_text(text="➡[💧SUI] Pool address?")
        context.user_data['state'] = FOR_SUI


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in stop_events:
        stop_events[chat_id].set() 
        print('stopped')
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
            emoji_use = '😄'
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
<b>Sui Buybot</b>

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

async def handle_message(update :Update , context:ContextTypes.DEFAULT_TYPE):
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
    if context.user_data['state'] == FOR_SUI:
        context.user_data['message'] = message_text 
        try:
            sui_address = context.user_data['message']
            token_info = get_token(sui_address)
            sui_check= check_group_exists(chat_id)
            if  sui_check == 'good':
                sui_db_token = fetch_token_address(chat_id)
                print('user already exist')
                await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {sui_db_token}',parse_mode='HTML',disable_web_page_preview=True)
            else:
                deep_down = token_info['data'][0]['attributes']
                if deep_down:
                    name = deep_down['name']
                    symbol = deep_down['symbol']
                    decimal = deep_down['decimals']
                    sui_done=insert_user(chat_id, sui_address,'','sui')
                    sol_db_token = fetch_token_address(chat_id)
                    ton_respnse = (
                                f"🎯 Sui Buybot is now tracking\n"
                                f"📈{sui_address}\n"
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
                    token_pools = get_token_pools(sui_address, page="1")
                    if token_pools:
                        start_suii(sui_address,context,chat_id,name,symbol)
                        context.user_data.clear()
                    else:
                        print("Failed to retrieve token pools.")
                        context.user_data.clear()
        except Exception as e:
            print(e)
            await context.bot.send_message(chat_id=chat_id, text='An Error Occured / Invalid Token address type /add to add a different pair address',parse_mode='HTML',disable_web_page_preview=True)
            context.user_data.clear()



def main():
    create_tables() 
    # start_price_updater_thread()
    app = ApplicationBuilder().token(TOKEN_KEY_).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler('remove', remove))
    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(add_query,pattern='^(sui)$'))
    app.add_handler(CallbackQueryHandler(done_too,pattern='^(confirm_remove|cancel_remove)$'))
    app.add_handler(CallbackQueryHandler(button,pattern='^(buybot_settings|close_menu)$'))
    app.add_handler(CallbackQueryHandler(another_query,pattern='^(gif_video|buy_emoji|buy_step|back_group_settings)$'))


    app.run_polling()


if __name__ == '__main__':
    main()