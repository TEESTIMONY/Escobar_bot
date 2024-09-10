import asyncio
from utils import get_token_price, get_weth_price_in_usd, format_market_cap, special_format
# from data_base import fetch_media_from_db, get_emoji_from_db, retrieve_group_number, chat_id_exists
from web3 import Web3
from utils import CONTRACT_ABI
import threading

import logging


async def handle_event(event, decimal, name, symbol, addr, pair, chat_id):
    try:
        trans_hash = event['transactionHash']
        TXN = trans_hash.hex()
        args = event['args']
        amount0In = args['amount0In']
        amount1In = args['amount1In']
        amount0Out = args['amount0Out']
        amount1Out = args['amount1Out']
        to = args['to']
        if (amount0In < amount0Out) and (amount1In >= amount1Out):
            current_price_usd = get_token_price(addr, pair)
            weth_price_usd = get_weth_price_in_usd()
            contract = Web3.eth.contract(address=addr, abi=CONTRACT_ABI)
            total_supply = Web3.from_wei(contract.functions.totalSupply().call(), 'ether')
            burn_address = '0x0000000000000000000000000000000000000000'
            burned_tokens = contract.functions.balanceOf(burn_address).call()
            circulating_supply = total_supply - burned_tokens
            MKT_cap = float(circulating_supply) * current_price_usd
            msg = (
                f'''
{amount0In}
{amount0Out}
{amount1In}
{amount1Out}'''
            )
            return msg
            # formatted_market_cap = format_market_cap(MKT_cap)
            # usd_value_bought = (float(amount1In) * 10**-18) * weth_price_usd
            # dec = int(decimal)
            # buy_step_number = retrieve_group_number(chat_id)
            # if buy_step_number is None:
            #     buy_step_number = 10
            # calc = int(usd_value_bought / buy_step_number)

            # emoji = get_emoji_from_db(chat_id)
            # if chat_id_exists(chat_id):
            #     if emoji:
            #         return (
            #             f"<b> ✅{name}</b> Buy!\n\n"
            #             f"{emoji * calc}\n"
            #             f"💵 {special_format(amount1In * 10**-18)} <b>ETH</b>\n"
            #             f"🪙{special_format(amount0Out * 10**-dec)} <b>{symbol}</b>\n"
            #             f"👤<a href='https://etherscan.io/address/{to[:7]}...{to[-4:]}'>{to[:7]}...{to[-4:]}</a>\n"
            #             f"🔷${special_format(usd_value_bought)}\n"
            #             f"🧢MKT Cap : ${special_format(MKT_cap)}\n\n"
            #             f"🦎<a href='https://dexscreener.com/ethereum/{pair}'>Chart</a> 🔷<a href='https://t.me/BSCTRENDING/5431871'>Trending</a>"
            #         )
            #     else:
            #         return (
            #             f"<b> ✅{name}</b> Buy!\n\n"
            #             f"{'🟢' * calc}\n"
            #             f"💵 {(amount1In * 10**-18)} <b>ETH</b>\n"
            #             f"🪙{(amount0Out * 10**-dec)} <b>{symbol}</b>\n"
            #             f"👤<a href='https://etherscan.io/address/{to[:7]}...{to[-4:]}'>{to[:7]}...{to[-4:]}</a>\n"
            #             f"🔷${(usd_value_bought)}\n"
            #             f"🧢MKT Cap : ${(MKT_cap)}\n\n"
            #             f"🦎<a href='https://dexscreener.com/ethereum/{pair}'>Chart</a> 🔷<a href='https://t.me/BSCTRENDING/5431871'>Trending</a>"
            #         )
    except Exception as e:
        print(e)

async def log_loop(event_filter, poll_interval):#, context, chat_id, decimal, name, symbol, addr, pair, stop_event
    while True:
        print('still running')
        for event in event_filter.get_new_entries():
            message = await handle_event(event) #, decimal, name, symbol, addr, pair, chat_id
            if message:
                print(message)
                # media = fetch_media_from_db(chat_id)
                # if media:
                #     file_id, file_type = media
                #     if file_type == 'photo':
                #         await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=message, parse_mode='HTML')
                #     elif file_type == 'gif':
                #         await context.bot.send_document(chat_id=chat_id, document=file_id, caption=message, parse_mode='HTML')
                # else:
                #     await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True)
        await asyncio.sleep(poll_interval)


def start_logging(event_filter, poll_interval,):# context, chat_id,decimal,name,symbol,addr,pair
    # if chat_id not in stop_events:
    #     stop_events[chat_id] = asyncio.Event()
    # stop_event = stop_events[chat_id]
    # stop_event.clear()
    try:

        asyncio.run_coroutine_threadsafe(
            log_loop(event_filter, poll_interval),#, context, chat_id,decimal,name,symbol,addr,pair,stop_event
            asyncio.get_event_loop()
        )

    except Exception as e:
        logging.error(f"Error in risky operation: {e}", exc_info=True)