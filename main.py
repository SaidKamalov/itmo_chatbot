from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from my_secrets import BOT_KEY


# Функция, которая будет вызываться при команде /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для отборочного задания")


def main() -> None:
    app = Application.builder().token(BOT_KEY).build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()
