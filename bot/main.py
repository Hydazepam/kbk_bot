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
from bot.database import init_db, save_message, is_user_authorized
# В начале файла добавьте:
from bot.database import get_all_messages

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для управления ответами.")

# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.message.reply_to_message:
#         user = update.effective_user
#         if is_user_authorized(user.id):  # Передаём числовой ID
#             # логика сохранения
#             original_msg = update.message.reply_to_message
#             reply_text = update.message.text
            
#             save_message(
#                 original_text=original_msg.text,
#                 reply_text=reply_text,
#                 user_id=user.id
#             )
            
#             # Отправка подтверждения с ответом на исходное сообщение
#             await update.message.reply_text(
#                 "✅ Ответ сохранён!",
#                 reply_to_message_id=update.message.reply_to_message.message_id
#             )

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