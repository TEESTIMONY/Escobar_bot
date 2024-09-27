

processed_signatures = set()  # Set to store logged signatures
process_cache = {"response": None, "last_updated": 0}

# Async function to fetch data
async def pump_fetch_data(url, headers, data, proxy):
    return requests.post(url, headers=headers, data=data, proxies=proxy).json()

async def pumpfun(token_address, interval, context, chat_id, stop_event, name, symbol, cache_expiry=60):
    try:
        while not stop_event.is_set():
            proxy = random.choice(proxies_list)
            url = "https://api.mainnet-beta.solana.com"
            headers = {"Content-Type": "application/json"}
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [token_address, {"limit": 10}]  # Fetching multiple signatures at once
            }

            # Use cache to reduce frequent API calls
            present_time = time.time()
            if present_time - process_cache['last_updated'] > cache_expiry or process_cache['response'] is None:
                response = await pump_fetch_data(url, headers, json.dumps(payload), proxy)
                process_cache['response'] = response
                process_cache['last_updated'] = present_time
            else:
                response = process_cache['response']

            if response and "result" in response:
                for txn in response['result']:
                    signature = txn['signature']

                    # Skip if the signature is already processed
                    if signature in processed_signatures:
                        continue

                    # Now process the new signature
                    payload2 = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                    }

                    response2 = requests.post(url, headers=headers, data=json.dumps(payload2))
                    res_data = response2.json()
                    messages = res_data['result']['meta']['logMessages']

                    if 'Program log: Instruction: Swap' in messages:
                        print("Detected a Swap transaction!")
                        # Log and process the swap

                    elif "Program log: Instruction: Buy" in messages:
                        signer = res_data['result']['transaction']['message']['accountKeys']
                        for items in signer:
                            if items['signer']:
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
                                if 'amount' in info:
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

                        # Prepare and send the message to the Telegram group
                        if token_amount and solana_amount:
                            supply = get_token_supply_mc_cap(token_address)
                            mk = float(solana_amount / token_amount) * supply
                            Mkt_cap = mk * float(retrieve_solana_price_from_db()['price'])

                            emoji = get_emoji_from_db(chat_id)
                            usd_value_bought = solana_amount * float(retrieve_solana_price_from_db()['price'])
                            buy_step_number = retrieve_group_number(chat_id) or 10
                            calc = int(usd_value_bought / buy_step_number)

                            if chat_id_exists(chat_id):
                                message = (
                                    f"<b> ✅{name}</b> Buy!\n\n"
                                    f"{emoji * calc if emoji else '🟢' * calc}\n"
                                    f"💵 {special_format(solana_amount)} <b>SOL</b>\n"
                                    f"🪙{special_format(token_amount)} <b>{symbol}</b>\n"
                                    f"🔷${special_format(usd_value_bought)}\n"
                                    f"🧢MKT Cap : ${special_format(Mkt_cap)}\n"
                                )

                                # Send media or message to the chat
                                media = fetch_media_from_db(chat_id)
                                if media:
                                    file_id, file_type = media
                                    if file_type == 'photo':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=message, parse_mode='HTML'),
                                            asyncio.get_event_loop()
                                        )
                                    elif file_type == 'gif':
                                        asyncio.run_coroutine_threadsafe(
                                            context.bot.send_document(chat_id=chat_id, document=file_id, caption=message, parse_mode='HTML'),
                                            asyncio.get_event_loop()
                                        )
                                else:
                                    asyncio.run_coroutine_threadsafe(
                                        context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', disable_web_page_preview=True),
                                        asyncio.get_event_loop()
                                    )

                    # Mark the signature as processed
                    processed_signatures.add(signature)

            await asyncio.sleep(interval)
    except Exception as e:
        print(f"Error in pumpfun: {e}")
