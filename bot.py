
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,ChatMemberHandler,CallbackQueryHandler,ConversationHandler,MessageHandler,filters
import asyncio
# Import your custom modules
from handlers import start,add,add_query,sol_query,settings,button,remove,done_too,another_query,handle_emoji,handle_message
from data_base import create_tables
# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
TOKEN_='6717839241:AAEWxg1NVhJSLbe7BeFvu8z2b_hc1OJ-Eso'
def main():
    create_tables()
    app = ApplicationBuilder().token(TOKEN_).build()
    #========= Handlers =============#
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler('remove', remove))
    app.add_handler(CommandHandler('settings', settings))
    #  # Register the chat member handler to detect when the bot is added to a group
    # app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    # app.add_handler(ChatMemberHandler(bot_removed_from_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(add_query,pattern='^(eth|bsc|ton|base|sol)$'))
    app.add_handler(CallbackQueryHandler(done_too,pattern='^(confirm_remove|cancel_remove)$'))
    app.add_handler(CallbackQueryHandler(button,pattern='^(buybot_settings|close_menu)$'))
    app.add_handler(CallbackQueryHandler(another_query,pattern='^(gif_video|buy_emoji|buy_step|back_group_settings)$'))
    app.add_handler(CallbackQueryHandler(sol_query,pattern='^(pumpfun|moonshot|pinksale|Dex)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # app.add_handler(MessageHandler(filters.PHOTO | filters.ANIMATION, handle_media))
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()