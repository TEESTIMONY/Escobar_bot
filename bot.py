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
CHOOSING,FOR_ETH =range(2)

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
    f"<b>🎉 Welcome to Sui Buyboy Bot!</b>\n\n"
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
<B>💼Escobar</b>
Choose a Chain ⛓️'''
                keyboard = [
                [InlineKeyboardButton("💧SUI", callback_data='eth')],
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
        await query.edit_message_text(text="➡[💧SUI] Token address?")
        context.user_data['state'] = FOR_ETH

def main():
    # create_tables()
    # start_price_updater_thread()
    app = ApplicationBuilder().token(TOKEN_KEY_).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == '__main__':
    main()