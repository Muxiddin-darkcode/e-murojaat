from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton
)
from database.models import UserType


def get_user_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🎓 Talaba", callback_data="register_type:TALABA")],
        [InlineKeyboardButton(text="👤 Fuqaro", callback_data="register_type:FUQARO")],
        [InlineKeyboardButton(text="👨‍👩‍👧 Ota-ona", callback_data="register_type:OTA_ONA")],
        [InlineKeyboardButton(text="🏢 Institut xodimi", callback_data="register_type:XODIM")],
        [InlineKeyboardButton(text="👥 Boshqa", callback_data="register_type:BOSHQA")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_course_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1-kurs", callback_data="course:1"),
            InlineKeyboardButton(text="2-kurs", callback_data="course:2")
        ],
        [
            InlineKeyboardButton(text="3-kurs", callback_data="course:3"),
            InlineKeyboardButton(text="4-kurs", callback_data="course:4")
        ],
        [
            InlineKeyboardButton(text="Magistratura", callback_data="course:5")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_relationship_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Onasi", callback_data="rel:Onasi"),
            InlineKeyboardButton(text="Otasi", callback_data="rel:Otasi")
        ],
        [
            InlineKeyboardButton(text="Vasiy / Qarindosh", callback_data="rel:Vasiy")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_consent_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Roziman va tasdiqlayman", callback_data="consent:agree", style="success")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="consent:decline", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_actions_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Ma'lumotlarni tahrirlash", callback_data="profile:edit", style="primary")],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="profile:refresh", style="primary")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_edit_fields_keyboard(user_type: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="👤 F.I.Sh.", callback_data="edit_field:full_name")],
        [InlineKeyboardButton(text="📱 Telefon raqam", callback_data="edit_field:phone")],
    ]
    if user_type == UserType.TALABA.value:
        buttons.extend([
            [InlineKeyboardButton(text="📚 Ta'lim yo'nalishi", callback_data="edit_field:direction")],
            [InlineKeyboardButton(text="🎓 Kursi", callback_data="edit_field:course")],
            [InlineKeyboardButton(text="👥 Guruh raqami", callback_data="edit_field:group_number")],
        ])
    elif user_type == UserType.FUQARO.value:
        buttons.append([InlineKeyboardButton(text="📍 Yashash hududi", callback_data="edit_field:region")])
    elif user_type == UserType.OTA_ONA.value:
        buttons.extend([
            [InlineKeyboardButton(text="👪 Qarindoshlik", callback_data="edit_field:parent_relation")],
            [InlineKeyboardButton(text="👥 Farzand guruhi", callback_data="edit_field:child_group")],
        ])
    else:
        buttons.append([InlineKeyboardButton(text="🏢 Tashkilot / Faoliyat", callback_data="edit_field:organization")])

    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="profile:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
