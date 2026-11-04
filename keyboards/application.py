from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import AppealType, AppealTopic


def get_appeal_types_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📄 Ariza", callback_data="app_type:ARIZA", style="primary")],
        [InlineKeyboardButton(text="⚠️ Shikoyat", callback_data="app_type:SHIKOYAT", style="danger")],
        [InlineKeyboardButton(text="💡 Taklif", callback_data="app_type:TAKLIF", style="primary")],
        [InlineKeyboardButton(text="❓ Savol", callback_data="app_type:SAVOL", style="primary")],
        [InlineKeyboardButton(text="🤝 Yordam so‘rash", callback_data="app_type:YORDAM", style="primary")],
        [InlineKeyboardButton(text="🙏 Tashakkurnoma", callback_data="app_type:TASHAKKURNOMA", style="success")],
        [InlineKeyboardButton(text="📌 Boshqa", callback_data="app_type:BOSHQA", style="primary")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_topics_keyboard(topics: List[AppealTopic]) -> InlineKeyboardMarkup:
    buttons = []
    for topic in topics:
        buttons.append([InlineKeyboardButton(text=topic.name, callback_data=f"app_topic:{topic.id}", style="primary")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_file_upload_keyboard(file_count: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    if file_count == 0:
        buttons.append([InlineKeyboardButton(text="➡️ Faylsiz davom etish", callback_data="file_action:skip", style="primary")])
    else:
        buttons.append([InlineKeyboardButton(text=f"✅ Fayllarni yakunlash ({file_count} ta yuklandi)", callback_data="file_action:done", style="success")])
    
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confidentiality_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🌐 Oddiy murojaat", callback_data="confidential:0", style="primary")],
        [InlineKeyboardButton(text="🔒 Maxfiy murojaat (Faqat Dekan uchun)", callback_data="confidential:1", style="danger")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_submission_confirm_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Murojaatni yuborish", callback_data="confirm_submit:yes", style="success")],
        [InlineKeyboardButton(text="✏️ Ma'lumotlarni tahrirlash", callback_data="confirm_submit:edit", style="primary")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

