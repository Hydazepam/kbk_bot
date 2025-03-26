import os
import signal
from telegram import Update
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, Conflict):
        print("🛑 Конфлікт виявлено! Виконую перезапуск...")
        await application.stop()
        os.kill(os.getpid(), signal.SIGTERM)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка повідомлень у групових чатах (адмін відповідає на повідомлення)
    if update.message.reply_to_message and update.message.chat.type in ['group', 'supergroup']:
        user = update.effective_user
        if is_user_authorized(user.id):
            original_msg = update.message.reply_to_message
            reply_text = update.message.text
            save_message(
                original_text=original_msg.text,
                reply_text=reply_text,
                user_id=user.id,
                is_private=False
            )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка приватних повідомлень від адміна
    user = update.effective_user
    if is_user_authorized(user.id):
        save_message(
            original_text=update.message.text,
            reply_text="",
            user_id=user.id,
            is_private=True
        )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Виведення всієї історії повідомлень (як з групових чатів, так і приватних)
    user = update.effective_user
    if is_user_authorized(user.id):
        try:
            messages = get_all_messages()  # Отримуємо усю історію
            response = "\n\n".join(
                [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2]}" + ("\n🔒 Private" if msg[3] else "")
                 for msg in messages]
            )
            await update.message.reply_text(response or "Історія порожня")
        except Exception as e:
            await update.message.reply_text(f"⛔ Помилка: {str(e)}")
    else:
        await update.message.reply_text("⛔ Доступ заборонено!")

if __name__ == "__main__":
    # Ініціалізація бази даних
    init_db()
    
    # Створення додатку
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Реєстрація команд та обробників повідомлень
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_admin_message))
    application.add_error_handler(error_handler)
    
    # Запуск бота з обробкою сигналів завершення
    application.run_polling(stop_signals=(signal.SIGINT, signal.SIGTERM), drop_pending_updates=True)