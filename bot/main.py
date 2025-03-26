import os
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
    # Ця функція більше не використовується, адже історію можна отримати через меню з кнопками.
    await update.message.reply_text("Використовуйте команду /menu для перегляду історії.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Створюємо inline клавіатуру з двома кнопками
    keyboard = [
        [InlineKeyboardButton("Загальна історія", callback_data="general_history")],
        [InlineKeyboardButton("Історія повідомлень в особисті", callback_data="private_history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Виберіть, яку історію переглянути:", reply_markup=reply_markup)

async def handle_history_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # обов'язково відповідаємо, щоб зник індикатор очікування
    messages = get_all_messages()
    
    if query.data == "general_history":
        # Фільтруємо лише записи з is_private=False
        filtered = [msg for msg in messages if not msg[3]]
        label = "Загальна історія"
    elif query.data == "private_history":
        # Фільтруємо лише записи з is_private=True
        filtered = [msg for msg in messages if msg[3]]
        label = "Історія повідомлень в особисті"
    else:
        filtered = []
        label = ""
        
    response = "\n\n".join(
        [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2]}" for msg in filtered]
    )
    if not response:
        response = "Історія порожня"
    await query.edit_message_text(text=f"{label}:\n\n{response}")

if __name__ == "__main__":
    # Ініціалізація бази даних
    init_db()
    
    # Створення додатку
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Реєстрація команд та обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_admin_message))
    application.add_handler(CallbackQueryHandler(handle_history_buttons))
    application.add_error_handler(error_handler)
    
    # Запуск бота з обробкою сигналів завершення
    application.run_polling(stop_signals=(signal.SIGINT, signal.SIGTERM), drop_pending_updates=True)