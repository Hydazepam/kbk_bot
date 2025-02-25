from telegram import Update, Bot, ReplyParameters
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from config import TOKEN, ADMIN_ID
from database import init_db, save_message, get_user_messages, is_user_authorized

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для управления ответами.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.chat.type in ['group', 'supergroup']:
        user = update.effective_user
        if is_user_authorized(user.id):
            original_msg = update.message.reply_to_message
            reply_text = update.message.text
            
            save_message(
                original_text=original_msg.text,
                reply_text=reply_text,
                user_id=user.id
            )
            
            await update.message.reply_text(
                f"Ответ сохранён!",
                reply_parameters=ReplyParameters(
                    message_id=update.message.message_id
                )
            )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_authorized(user.id):
        messages = get_user_messages(user.id)
        response = "\n\n".join(
            [f"Вопрос: {msg[0]}\nОтвет: {msg[1]}\nДата: {msg[2]}" 
             for msg in messages]
        )
        await update.message.reply_text(response or "Нет сохранённых сообщений")

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