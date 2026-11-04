from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Appeal, AppealStatus


def get_user_appeals_pagination(
    appeals: List[Appeal],
    current_page: int,
    total_count: int,
    limit: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_count + limit - 1) // limit)
    buttons = []

    for app in appeals:
        status_label = AppealStatus.label(app.status)
        buttons.append([
            InlineKeyboardButton(
                text=f"{app.appeal_number} | {status_label}",
                callback_data=f"user_app_view:{app.id}:{current_page}"
            )
        ])

    nav_row = []
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"user_app_page:{current_page - 1}")
        )
    nav_row.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{total_pages}", callback_data="noop")
    )
    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"user_app_page:{current_page + 1}")
        )

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="user_app_close")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_appeal_detail_keyboard(appeal_id: int, page: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💬 Dekanatga xabar / qo‘shimcha ma'lumot", callback_data=f"user_chat:{appeal_id}")],
        [InlineKeyboardButton(text="⬅️ Murojaatlar ro‘yxatiga qaytish", callback_data=f"user_app_page:{page}")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="user_app_close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_staff_assigned_keyboard(
    appeals: List[Appeal],
    current_page: int,
    total_count: int,
    limit: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_count + limit - 1) // limit)
    buttons = []

    for app in appeals:
        status_label = AppealStatus.label(app.status)
        buttons.append([
            InlineKeyboardButton(
                text=f"📌 {app.appeal_number} - {status_label}",
                callback_data=f"staff_view:{app.id}:{current_page}"
            )
        ])

    nav_row = []
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"staff_page:{current_page - 1}")
        )
    nav_row.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{total_pages}", callback_data="noop")
    )
    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"staff_page:{current_page + 1}")
        )
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="staff_close")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
