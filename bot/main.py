import os
import signal
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
from bot.database import get_db_connection, init_db, save_message, get_all_messages, is_user_authorized
from telegram.error import Conflict

# Глобальний прапорець для контролю циклу
running = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот для управління відповідями.")

async def stop_application():
    global running
    running = False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, Conflict):
        print("🛑 Конфлікт виявлено! Виконую перезапуск...")
        await application.stop()
        os.kill(os.getpid(), signal.SIGTERM)

async def handle_shutdown(signum, frame):
    print("🔴 Отримано сигнал завершення")
    await application.stop()
    exit(0)

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
        save_message(
            original_text="Адмін: " + update.message.text,
            reply_text="",
            user_id=user.id,
            is_private=True  # Явно указываем параметр
        )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_authorized(user.id):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT original_text, reply_text, message_date 
                        FROM messages 
                        WHERE user_id = %s
                        ORDER BY message_date DESC
                    """, (user.id,))
                    messages = cur.fetchall()
            
            response = "\n\n".join(
                [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2]}" 
                 for msg in messages]
            )
            await update.message.reply_text(response or "Історія порожня")
        except Exception as e:
            await update.message.reply_text(f"⛔ Помилка: {str(e)}")
    else:
        await update.message.reply_text("⛔ Доступ заборонено!")

if __name__ == "__main__":
    # Ініціалізація БД
    init_db()
    
    # Створення додатку
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Реєстрація обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    application.add_error_handler(error_handler)
    
    # Обробка сигналів
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Запуск з автоматичним перезапуском
    while running:
        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            while running:
                await asyncio.sleep(1)
        except Conflict as e:
            print(f"⚠️ Конфлікт: {e}")
            await application.stop()
            await asyncio.sleep(5)  # Затримка перед перезапуском
        finally:
            await application.stop()

# if __name__ == "__main__":
#     init_db()
    
#     application = ApplicationBuilder().token(TOKEN).build()
    
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("history", show_history))
#     application.add_handler(MessageHandler(
#         filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
#         handle_message
#     ))
#     application.add_handler(
#         MessageHandler(
#             filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
#             handle_admin_message
#         )
#     )    
#     application.run_polling(
# #       stop_signals=(SIGINT, SIGTERM),
# #       close_loop=False,
# #       drop_pending_updates=True  # Игнорировать старые сообщения
#     )
#     application.add_error_handler(error_handler)
