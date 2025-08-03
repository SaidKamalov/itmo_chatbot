from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from my_secrets import BOT_KEY
from config import STUDY_PROGRAMS

# List of available study programs (example)
study_programm_list = [v["name"] for k, v in STUDY_PROGRAMS.items()]


# Start command handler (shows "Start" button)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("Start")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Нажмите 'Start' чтобы начать.", reply_markup=reply_markup
    )


# Handler for text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text

    if user_text == "Start":
        # After pressing Start, show "Show Study Programs" button
        keyboard = [[KeyboardButton("Show Study Programs")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Привет! Я бот для отборочного задания.\nНажмите 'Show Study Programs', чтобы посмотреть доступные программы.",
            reply_markup=reply_markup,
        )
    elif user_text == "Show Study Programs":
        # Show list of study programs and instructions
        programs_str = "\n".join(f"- {p}" for p in study_programm_list)
        await update.message.reply_text(
            f"Список программ:\n{programs_str}\n\nНапишите название программы, чтобы узнать подробности.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(p)] for p in study_programm_list], resize_keyboard=True
            ),
        )
    elif user_text in study_programm_list:
        description = [
            v["description"]
            for k, v in STUDY_PROGRAMS.items()
            if v["name"] == user_text
        ]
        await update.message.reply_text(
            f"Подробнее о программе {user_text}:\n {description[0]}"
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите одну из предложенных опций."
        )


def main():
    app = Application.builder().token(BOT_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
