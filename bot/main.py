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

# Постійна клавіатура для приватного чату
persistent_keyboard = ReplyKeyboardMarkup(
    [["Загальна історія", "Історія повідомлень в особисті"]],
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
    # Обробка приватних повідомлень, які НЕ відповідають варіантам з клавіатури
    user = update.effective_user
    if is_user_authorized(user.id) and update.message.text not in ["Загальна історія", "Історія повідомлень в особисті"]:
        save_message(
            original_text=update.message.text,
            reply_text="",
            user_id=user.id,
            is_private=True
        )
        await update.message.reply_text("Повідомлення збережено.", reply_markup=persistent_keyboard)

async def handle_history_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обробка натискання кнопок (повідомлення дорівнює тексту кнопки)
    text = update.message.text
    messages = get_all_messages()
    if text == "Загальна історія":
        filtered = [msg for msg in messages if not msg[3]]  # is_private=False
        label = "Загальна історія"
    elif text == "Історія повідомлень в особисті":
        filtered = [msg for msg in messages if msg[3]]  # is_private=True
        label = "Історія повідомлень в особисті"
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
    # Хендлер, який спрацьовує, коли у приватному чаті отримуємо повідомлення, що збігається з текстом кнопок
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & filters.Regex("^(Загальна історія|Історія повідомлень в особисті)$"),
        handle_history_choice
    ))
    # Обробка інших приватних повідомлень (не з клавіатури)
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_admin_message))
    # Обробка повідомлень у групових чатах
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_message))
    application.add_error_handler(error_handler)
    
    # Запуск бота з обробкою сигналів завершення
    application.run_polling(stop_signals=(signal.SIGINT, signal.SIGTERM), drop_pending_updates=True)