from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(is_staff: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        # Asosiy harakat tugmasi - Yashil fon (style="success"), to'liq qatorda
        [KeyboardButton(text="📝 Murojaat yuborish", style="success")],
        
        # 2 ta qisqa tugma - Ko'k fon (style="primary")
        [
            KeyboardButton(text="📂 Mening murojaatlarim", style="primary"),
            KeyboardButton(text="🔎 Holatni tekshirish", style="primary")
        ],
        
        # Dekanat bilan yozishmalar - Ko'k fon (style="primary"), to'liq qatorda
        [KeyboardButton(text="💬 Dekanat bilan yozishmalar", style="primary")],
        
        # Profil va Bog'lanish - Ko'k fon (style="primary")
        [
            KeyboardButton(text="👤 Mening profilim", style="primary"),
            KeyboardButton(text="📞 Bog‘lanish", style="primary")
        ],
        
        # Bot haqida - Odatiy/Primary
        [KeyboardButton(text="ℹ️ Bot haqida", style="primary")]
    ]
    if is_staff:
        # Mas'ullar uchun - Qizil fon (style="danger")
        keyboard.append([KeyboardButton(text="⚡️ Boshqaruv paneli (/admin)", style="danger")])
        
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo'limni tanlang..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish", style="danger")]],
        resize_keyboard=True
    )


def get_back_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Orqaga", style="primary"), KeyboardButton(text="❌ Bekor qilish", style="danger")]
        ],
        resize_keyboard=True
    )
