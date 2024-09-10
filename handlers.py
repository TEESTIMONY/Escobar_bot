from telegram import Update
from telegram.ext import ContextTypes
from telegram import Chat, ChatMember, ChatMemberUpdated, Update,InlineKeyboardMarkup, InlineKeyboardButton
from data_base import retrieve_group_number,get_emoji_from_db,fetch_pair_address_and_blockchain_for_group,fetch_token_address,delete_chat_id,save_emoji_to_db,save_or_update_group_buy_number,download_file,save_or_update_media_in_db ,check_group_exists,insert_user
from utils import is_valid_ethereum_address,get_pair_address,get_token_details,web3,PAIR_ABI
CHOOSING,FOR_ETH,FOR_BSC,FOR_BASE,FOR_TON,FOR_PUMP,SEND_MEDIA,FOR_MOON,FOR_PINK,FOR_DEXES = range(10)
from events import start_logging
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type: str = update.message.chat.type
    chat_id = update.message.from_user.id
    if chat_type == 'private':
        welcome_message = (
            "<b>🎉 Welcome to Escobar Bot!</b>\n\n"
            "I'm here to help you manage your web3 activities effortlessly. Here’s what I can do:\n\n"
            "🟢 <b>/start</b> - Start your journey with Escobar.\n"
            "⚙️ <b>/settings</b> - Customize your experience and adjust your preferences.\n"
            "❌ <b>/remove</b> - Remove a token with ease (confirmation required).\n"
            "➕ <b>/add</b> - Add a new token to your list.\n"
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_message, parse_mode='HTML', disable_web_page_preview=True)
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
    if chat_type == 'supergroup' or chat_type == 'group':
        chat_id = update.effective_chat.id
        print(chat_id)

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
    # elif chat_type == 'group':
    #     await update.message.reply_text("Your Group is not a supergroup, make it a super group")
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
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text="➡[⚡SOL] Token address?",reply_markup=reply_markup)
        # context.user_data['state'] = FOR_SOL
    elif query.data =='ton':
        await query.edit_message_text(text="➡[💡TON(📦DeDust)] Pair address?")
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
        buy_number =await retrieve_group_number(chat_id)
        print(buy_number)
        if buy_number == None:
            buy_number_use = 10
        else:
            buy_number_use = buy_number
        emoji = await get_emoji_from_db(chat_id)
        if emoji:
            emoji_use = emoji
        else:
            emoji_use = '🟢'
        try:
            pair_adress,blockchain =await fetch_pair_address_and_blockchain_for_group(chat_id)
            pair_adress = pair_adress
            blockchain = blockchain
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

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # if chat_id in stop_events:
    #     stop_events[chat_id].set() 
    #     print('stopped')
    # else:
    #     print('fuck')

    chat_type: str = update.message.chat.type
    if chat_type == 'group' or chat_type == 'supergroup':
        chat_id = update.effective_chat.id
        if not await is_user_admin(update, context):
            await update.message.reply_text("You're not authorized to use this bot")
        else:   
            bot_chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if bot_chat_member.status == "administrator":
                group_token = await fetch_token_address(chat_id)
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
        chat_id_to_delete = chat_id
        await delete_chat_id(chat_id_to_delete)
        await query.edit_message_text(text="Token has been removed successfully.")

    elif query.data == 'cancel_remove':
        await query.edit_message_text(text="Token removal has been cancelled.")
    
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
            print('you clicked gif_video')
            await query.edit_message_text(text="Send me a image/gif")

        elif query.data == 'buy_emoji':
            await query.edit_message_text(text="Please send emoji")
            context.user_data['awaiting_emoji'] = True
        elif query.data == 'buy_step':
            await query.edit_message_text(text="Send me a number for your buy step")
            # print(query.message)
            context.user_data['awaiting_number'] = True
        elif query.data == 'back_group_settings':
            btn2= InlineKeyboardButton("🟢 BuyBot Settings", callback_data='buybot_settings')
            btn9= InlineKeyboardButton("🔴 Close menu", callback_data='close_menu')

            row2= [btn2]
            row9= [btn9]
            reply_markup_pair = InlineKeyboardMarkup([row2,row9])
            await query.edit_message_reply_markup(reply_markup=reply_markup_pair)
    else:
        print('hANDLE DIFFERENTLY')

async def handle_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    chat_id = update.effective_chat.id
    if user_data.get('awaiting_emoji'):
        emoji = update.message.text
        if emoji:
            await save_emoji_to_db(emoji, chat_id)
            await update.message.reply_text(f'Emoji {emoji} saved to database.')
            user_data['awaiting_emoji'] = False
        else:
            await update.message.reply_text('Please send a valid emoji.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    message_text = update.message.text
    if context.user_data.get('awaiting_emoji'):
        emoji = update.message.text
        if emoji:
            await save_emoji_to_db(emoji, update.effective_chat.id)
            await update.message.reply_text(f'Emoji {emoji} saved to database.')
            context.user_data['awaiting_emoji'] = False
        else:
            await update.message.reply_text('Please send a valid emoji.')

    elif context.user_data.get('awaiting_number'):
        try:
            buy_step_number = update.message.text
            await save_or_update_group_buy_number(chat_id,buy_step_number)
            await update.message.reply_text('Buy Step saved.')
            context.user_data['awaiting_number'] = False
        except Exception as e:
            await update.message.reply_text('Send a valid number')
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
        try:
            if 'state' in context.user_data:
                if context.user_data['state'] == FOR_ETH:
                    context.user_data['message'] = message_text
                    if await is_valid_ethereum_address(context.user_data['message']):
                        token_address =context.user_data['message']
                        # Get pair address
                        pair_address = await get_pair_address(token_address)
                        block_chain = 'ethereum'
                        if pair_address == '0x0000000000000000000000000000000000000000':
                            await context.bot.send_message(chat_id=chat_id, text=f'No pair found for the given token type "/add" to add a different Token',parse_mode='HTML',disable_web_page_preview=True)
                        else:
                            token_address =context.user_data['message']
                            token_name, token_symbol ,token_decimal= await get_token_details(token_address)
                            ghcall= await check_group_exists(chat_id)
                            if  ghcall == 'good':
                                # db_token = await fetch_token_address(chat_id)
                                await context.bot.send_message(chat_id=chat_id, text=f'❗️Bot already in use in this group for token {token_address}',parse_mode='HTML',disable_web_page_preview=True)
                            else:
                                await insert_user(chat_id, token_address,pair_address,block_chain)
                                # db_token =await fetch_token_address(chat_id)
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
                                print('surpossed stat')
                                print(token_name,token_symbol,token_decimal)
                                print(token_address)

                                swapping_pair_address =await get_pair_address(token_address)
                                # Create a filter for the Swap event
                                pair_contract = web3.eth.contract(address=swapping_pair_address, abi=PAIR_ABI)

                                swap_event_filter = pair_contract.events.Swap.create_filter(fromBlock='latest')
                                # Start monitoring the swap events
                                print('started')
                                start_logging(swap_event_filter, 2)# context, chat_id,token_decimal,token_name,token_symbol,token_address,pair_address
        except KeyboardInterrupt:
            print("Stopped monitoring swap events")
        except IndexError:
            print('error: ',e)