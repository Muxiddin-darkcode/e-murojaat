from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(is_staff: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📝 Murojaat yuborish"), KeyboardButton(text="📂 Mening murojaatlarim")],
        [KeyboardButton(text="🔎 Murojaat holatini tekshirish"), KeyboardButton(text="💬 Dekanat bilan yozishmalar")],
        [KeyboardButton(text="👤 Mening profilim"), KeyboardButton(text="📞 Bog‘lanish")],
        [KeyboardButton(text="ℹ️ Bot haqida")]
    ]
    if is_staff:
        keyboard.append([KeyboardButton(text="⚡️ Boshqaruv paneli (/admin)")])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo'limni tanlang..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def get_back_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
