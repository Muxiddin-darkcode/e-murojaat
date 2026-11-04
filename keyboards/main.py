from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(is_staff: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        # Asosiy harakat tugmasi - to'liq kenglikda (Yashil)
        [KeyboardButton(text="🟢 📝 Murojaat yuborish")],
        
        # 2 ta ixcham tugma - 1 qatorda chiroyli sig'adi (Ko'k va Binafsha)
        [
            KeyboardButton(text="🔵 📂 Murojaatlarim"),
            KeyboardButton(text="🟣 🔎 Holatni tekshirish")
        ],
        
        # To'liq kenglikdagi yozishmalar tugmasi (mobil ekranda matn buzulmaydi)
        [KeyboardButton(text="💬 🏛 Dekanat bilan yozishmalar")],
        
        # Profil va Bog'lanish tugmalari
        [
            KeyboardButton(text="👤 📋 Mening profilim"),
            KeyboardButton(text="📞 📲 Bog‘lanish")
        ],
        
        # Bot haqida
        [KeyboardButton(text="ℹ️ 📖 Bot haqida")]
    ]
    if is_staff:
        keyboard.append([KeyboardButton(text="🔴 ⚡️ Boshqaruv paneli (/admin)")])
        
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

