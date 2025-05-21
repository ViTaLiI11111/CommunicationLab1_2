from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def format_answers_as_inline_keyboard(question):
    keyboard = []
    for char, answer_text in question.question_answers.items():
        callback_data = f"answer:{char}"
        keyboard.append([InlineKeyboardButton(f"{char}. {answer_text}", callback_data=callback_data)])

    return InlineKeyboardMarkup(keyboard)