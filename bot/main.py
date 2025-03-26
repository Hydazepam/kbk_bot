import os
import signal
from telegram import Update, ReplyKeyboardMarkup
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

# Постійна клавіатура для приватного чату з кнопками
persistent_keyboard = ReplyKeyboardMarkup(
    [["chat mssg", "private mssg"]],
    one_time_keyboard=False,
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # В приватному чаті надсилаємо повідомлення з постійною клавіатурою
    if update.message.chat.type == "private":
        await update.message.reply_text(
            "Привіт! Я бот для управління відповідями. Оберіть опцію:",
            reply_markup=persistent_keyboard
        )
    else:
        await update.message.reply_text("Привіт! Я бот для управління відповідями.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, Conflict):
        print("🛑 Конфлікт виявлено! Виконую перезапуск...")
        try:
            await application.stop()
        except RuntimeError as e:
            print("Application is not running:", e)
        os.kill(os.getpid(), signal.SIGTERM)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка повідомлень у групових чатах:
    # Бот зберігатиме відповідь лише тоді, коли адмін відмічає бота (тобто, у тексті є згадка @bot_username)
    if update.message.reply_to_message and update.message.chat.type in ['group', 'supergroup']:
        user = update.effective_user
        if is_user_authorized(user.id):
            bot_username = context.bot.username  # Отримуємо ім'я бота
            if "@" + bot_username in update.message.text:
                original_msg = update.message.reply_to_message
                reply_text = update.message.text
                save_message(
                    original_text=original_msg.text,
                    reply_text=reply_text,
                    user_id=user.id,
                    is_private=False
                )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка приватних повідомлень (без змін)
    user = update.effective_user
    if is_user_authorized(user.id) and update.message.text not in ["chat mssg", "private mssg"]:
        save_message(
            original_text=update.message.text,
            reply_text="",
            user_id=user.id,
            is_private=True
        )
        await update.message.reply_text("Повідомлення збережено.", reply_markup=persistent_keyboard)

async def handle_history_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка вибору з клавіатури (повідомлення дорівнює тексту кнопки)
    text = update.message.text
    messages = get_all_messages()
    if text == "chat mssg":
        filtered = [msg for msg in messages if not msg[3]]  # is_private=False
        label = "chat mssg"
    elif text == "private mssg":
        filtered = [msg for msg in messages if msg[3]]  # is_private=True
        label = "private mssg"
    else:
        return
    # Форматуємо дату: година, хвилина, число, місяць, рік
    response = "\n\n".join(
        [f"❓: {msg[0]}\n✅: {msg[1]}\n📅: {msg[2].strftime('%H:%M %d.%m.%Y')}" for msg in filtered]
    )
    if not response:
        response = "Історія порожня"
    await update.message.reply_text(f"{label}:\n\n{response}", reply_markup=persistent_keyboard)

if __name__ == "__main__":
    # Ініціалізація бази даних
    init_db()
    
    # Створення додатку
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Реєстрація команд та обробників
    application.add_handler(CommandHandler("start", start))
    # Хендлер для вибору історії через клавіатуру (фільтр для точного співпадіння тексту кнопок)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & filters.Regex("^(chat mssg|private mssg)$"),
        handle_history_choice
    ))
    # Обробка інших приватних повідомлень (не з клавіатури)
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_admin_message))
    # Обробка повідомлень у групових чатах
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    application.add_error_handler(error_handler)
    
    # Запуск бота з обробкою сигналів завершення
    application.run_polling(stop_signals=(signal.SIGINT, signal.SIGTERM), drop_pending_updates=True)