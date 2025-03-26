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
    await update.message.reply_text("Привіт! Я бот для управління відповідями.")

# async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if isinstance(context.error, Conflict):
#         print("⚠️ Обнаружен конфликт версий бота! Останавливаюсь...")
#         await context.application.stop()
#         exit(1)
#     else:
#         print(f"⚠️ Ошибка: {context.error}")

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

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_authorized(user.id):
        # Зберігаємо повідомлення адміна як окремий запис
        save_message(
            original_text="Адмін: " + update.message.text,
            reply_text="",
            user_id=user.id,
            is_private=True
        )
        await update.message.reply_text("📝 Ваше повідомлення збережено!")

# async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.effective_user
#     if is_user_authorized(user.id):
#         messages = get_all_messages()  # Теперь функция доступна
        
#         response = "\n\n".join(
#             [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2]}" 
#              for msg in messages]
#         )
        
#         await update.message.reply_text(response or "Історія порожня")
#     else:
#         await update.message.reply_text("⛔ Доступ заборонено!")
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_authorized(user.id):
        # Отримуємо всі записи
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT original_text, reply_text, message_date, is_private
                    FROM messages 
                    WHERE user_id = %s
                    ORDER BY message_date DESC
                """, (user.id,))
                messages = cur.fetchall()
        
        # Форматування
        public_msgs = [msg for msg in messages if not msg[3]]
        private_msgs = [msg for msg in messages if msg[3]]
        
        response = "📢 Групові записи:\n" + format_messages(public_msgs)
        response += "\n\n🔒 Ваші особисті записи:\n" + format_messages(private_msgs)
        
        await update.message.reply_text(response or "Історія порожня")

if __name__ == "__main__":
    init_db()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_message
    ))
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            handle_admin_message
        )
    )    
    application.run_polling(
#       stop_signals=(SIGINT, SIGTERM),
#       close_loop=False,
#       drop_pending_updates=True  # Игнорировать старые сообщения
    )
