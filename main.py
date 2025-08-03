from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import os
from my_secrets import BOT_KEY
from config import STUDY_PROGRAMS

# Define conversation states
START, SHOWING_PROGRAMS, PROGRAM_DETAILS = range(3)

# List of available study programs
study_program_list = [v["name"] for k, v in STUDY_PROGRAMS.items()]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    keyboard = [[KeyboardButton("Start")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Нажмите 'Start' чтобы начать.", reply_markup=reply_markup
    )

    return START


async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the 'Start' button press and move to showing programs state."""
    keyboard = [[KeyboardButton("Show Study Programs")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Привет! Я бот для отборочного задания.\nНажмите 'Show Study Programs', чтобы посмотреть доступные программы.",
        reply_markup=reply_markup,
    )

    return SHOWING_PROGRAMS


async def show_programs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of study programs and move to program details state."""
    programs_str = "\n".join(f"- {p}" for p in study_program_list)

    # Create keyboard with program buttons
    keyboard = [[KeyboardButton(p)] for p in study_program_list]
    # Add a button to go back to start
    keyboard.append([KeyboardButton("◀️ Back to Start")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Список программ:\n{programs_str}\n\nНапишите название программы, чтобы узнать подробности.",
        reply_markup=reply_markup,
    )

    return PROGRAM_DETAILS


async def show_program_details(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show details for a specific program and offer to download the study plan."""
    user_text = update.message.text

    # Handle back button
    if user_text == "◀️ Back to Start":
        return await start_conversation(update, context)

    # Check if the user requested a PDF download
    if user_text == "📄 Скачать учебный план":
        # Get the selected program from context
        selected_program = context.user_data.get("selected_program")
        if selected_program:
            # Find the local path for this program
            local_path = None

            for url, info in STUDY_PROGRAMS.items():
                if info["name"] == selected_program:
                    local_path = info.get("path_to_study_plan")
                    break

            if local_path and os.path.exists(local_path):
                # We have the file locally, send it
                try:
                    await update.message.reply_document(
                        document=open(local_path, "rb"),
                        filename=f"Учебный план - {selected_program}.pdf",
                        caption=f"Учебный план для программы '{selected_program}'",
                    )

                    # Create keyboard with program options
                    keyboard = [
                        [KeyboardButton("🔄 Выбрать другую программу")],
                        [KeyboardButton("◀️ Back to Start")],
                    ]

                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

                    await update.message.reply_text(
                        "Что вы хотите сделать дальше?", reply_markup=reply_markup
                    )
                except Exception as e:
                    await update.message.reply_text(
                        f"Ошибка при отправке файла: {str(e)}"
                    )
            else:
                await update.message.reply_text(
                    "К сожалению, файл учебного плана не найден."
                )

            return PROGRAM_DETAILS
        else:
            await update.message.reply_text("Сначала выберите программу обучения.")
            return await show_programs(update, context)

    # Find the program details
    if user_text in study_program_list:
        # Save the selected program in context
        context.user_data["selected_program"] = user_text

        # Get program description
        description = None
        for k, v in STUDY_PROGRAMS.items():
            if v["name"] == user_text:
                description = v.get("description")
                break

        if not description:
            description = "Описание программы отсутствует."

        # Create keyboard with program options
        keyboard = [
            [KeyboardButton("📄 Скачать учебный план")],
            [KeyboardButton("◀️ Back to Start")],
            [KeyboardButton("🔄 Выбрать другую программу")],
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"Подробнее о программе {user_text}:\n\n{description}\n\n"
            "Нажмите '📄 Скачать учебный план' чтобы получить PDF документ с учебным планом.",
            reply_markup=reply_markup,
        )

        return PROGRAM_DETAILS
    elif user_text == "🔄 Выбрать другую программу":
        return await show_programs(update, context)
    else:
        await update.message.reply_text(
            "Программа не найдена. Пожалуйста, выберите одну из предложенных опций."
        )

        # Show programs again
        return await show_programs(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Разговор завершен. Для начала нового разговора отправьте /start.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def main():
    """Start the bot."""
    app = Application.builder().token(BOT_KEY).build()

    # Create the conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.Regex("^Start$"), start_conversation)],
            SHOWING_PROGRAMS: [
                MessageHandler(filters.Regex("^Show Study Programs$"), show_programs)
            ],
            PROGRAM_DETAILS: [
                MessageHandler(
                    filters.Regex("^📄 Скачать учебный план$"), show_program_details
                ),
                MessageHandler(
                    filters.Regex("^🔄 Выбрать другую программу$"), show_programs
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, show_program_details),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Start the Bot
    app.run_polling()


if __name__ == "__main__":
    main()
