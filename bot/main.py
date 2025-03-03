from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from bot.config import TOKEN, ADMIN_ID, DB_URL
from bot.database import init_db, save_message, get_all_messages, is_user_authorized
from telegram.error import Conflict

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для управления ответами.")

# async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if isinstance(context.error, Conflict):
#         print("⚠️ Обнаружен конфликт версий бота! Останавливаюсь...")
#         await context.application.stop()
#         exit(1)
#     else:
#         print(f"⚠️ Ошибка: {context.error}")

# if __name__ == "__main__":
#     application = ApplicationBuilder().token(TOKEN).build()
    
#     # Регистрация обработчиков
#     application.add_error_handler(error_handler)
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("history", show_history))
#     application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    
#     # Запуск с контролем версий
#     application.run_polling(
#         stop_signals=(SIGINT, SIGTERM),
#         close_loop=False,
#         drop_pending_updates=True  # Игнорировать старые сообщения
#     )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.chat.type in ['group', 'supergroup']:
        user = update.effective_user
        if is_user_authorized(user.id):
            original_msg = update.message.reply_to_message
            reply_text = update.message.text
            
            save_message(
                original_text=original_msg.text,
                reply_text=reply_text
            )
            
            # Удалите эту строку:
            # await update.message.reply_text("✅ Ответ сохранён!")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_authorized(user.id):
        messages = get_all_messages()  # Теперь функция доступна
        
        response = "\n\n".join(
            [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2]}" 
             for msg in messages]
        )
        
        await update.message.reply_text(response or "Історія порожня")
    else:
        await update.message.reply_text("⛔ Доступ заборонено!")

if __name__ == "__main__":
    init_db()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_message
    ))
    
    application.run_polling()

# if __name__ == "__main__":
#     application = ApplicationBuilder().token(TOKEN).build()
      
#     # Регистрация обработчиков
#     application.add_error_handler(error_handler)
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("history", show_history))
#     application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
      
#     # Запуск с контролем версий
#     application.run_polling(
#       stop_signals=(SIGINT, SIGTERM),
#       close_loop=False,
#       drop_pending_updates=True  # Игнорировать старые сообщения
#     )