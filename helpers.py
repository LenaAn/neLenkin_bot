from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton


def get_user(update: Update):
    if hasattr(update, "callback_query") and update.callback_query:
        return update.callback_query.from_user
    if hasattr(update, "message") and update.message:
        return update.message.from_user


def main_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Как вступить?", callback_data="how_to_join"),
        InlineKeyboardButton("Хочу читать Кабанчика!", callback_data="ddia"),
        InlineKeyboardButton("Хочу читать SRE Book!", callback_data="sre_book"),
        InlineKeyboardButton("LeetCode мок-собеседования!", callback_data="mock_leetcode")
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)


def back_menu() -> InlineKeyboardMarkup:
    button_list = [
        InlineKeyboardButton("Назад", callback_data="back"),
    ]
    menu = [button_list[i:i + 1] for i in range(0, len(button_list), 1)]
    return InlineKeyboardMarkup(menu)