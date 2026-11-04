import logging
import os
import shutil
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import User, UserRole, AppealTopic
from database.queries import (
    get_or_create_user, get_all_topics, add_topic, toggle_topic_status
)
from keyboards.admin import get_settings_menu
from states.admin import AdminSettingsState
from utils.helpers import get_setting, set_setting, log_audit

logger = logging.getLogger(__name__)
router = Router(name="admin_settings_router")


@router.callback_query(F.data == "admin_nav:settings")
async def show_settings_main(callback: CallbackQuery, session: AsyncSession):
    user = await get_or_create_user(session, callback.from_user.id)
    is_super = (settings.SUPER_ADMIN_ID and callback.from_user.id == settings.SUPER_ADMIN_ID) or user.role == UserRole.SUPER_ADMIN.value

    if not is_super:
        await callback.answer("Bot sozlamalari faqat Bosh administrator uchun!", show_alert=True)
        return

    inst = await get_setting(session, "institute_name")
    dept = await get_setting(session, "department_name")
    dekan = await get_setting(session, "dekan_name")
    phone = await get_setting(session, "contact_phone")
    tg = await get_setting(session, "official_telegram")
    deadline = await get_setting(session, "default_deadline_days")
    status = await get_setting(session, "appeals_enabled", "true")

    text = (
        "⚙️ <b>BOTNING ASOSIY SOZLAMALARI</b>\n\n"
        f"🏛 <b>Institut:</b> {inst}\n"
        f"📚 <b>Kafedra:</b> {dept}\n"
        f"👤 <b>Dekan / Mudir:</b> {dekan}\n"
        f"📞 <b>Aloqa telefoni:</b> {phone}\n"
        f"✈️ <b>Rasmiy Telegram:</b> {tg}\n"
        f"⏱ <b>Standart ijro muddati:</b> {deadline} kun\n"
        f"🟢 <b>Murojaatlar qabuli:</b> {'Faol' if status.lower() == 'true' else 'Vaqtincha to‘xtatilgan'}\n\n"
        "O‘zgartirmoqchi bo‘lgan parametrni tanlang:"
    )

    buttons = [
        [InlineKeyboardButton(text="🏛 Institut nomi", callback_data="set_edit:institute_name")],
        [InlineKeyboardButton(text="📚 Kafedra nomi", callback_data="set_edit:department_name")],
        [InlineKeyboardButton(text="👤 Dekan F.I.Sh.", callback_data="set_edit:dekan_name")],
        [InlineKeyboardButton(text="📞 Aloqa telefoni", callback_data="set_edit:contact_phone")],
        [InlineKeyboardButton(text="✈️ Rasmiy Telegram", callback_data="set_edit:official_telegram")],
        [InlineKeyboardButton(text="⏱ Standart ijro muddati", callback_data="set_edit:default_deadline_days")],
        [InlineKeyboardButton(text="🗂 Yo‘nalishlarni boshqarish", callback_data="set_manage:topics")],
        [InlineKeyboardButton(text="🔄 Qabulni yoqish / o‘chirish", callback_data="set_toggle:appeals")],
        [InlineKeyboardButton(text="💾 Baza zaxira nusxasi (Backup)", callback_data="set_act:backup")],
        [InlineKeyboardButton(text="🏠 Admin menyu", callback_data="admin_nav:menu")]
    ]

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("set_edit:"))
async def edit_setting_param(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    key = callback.data.split(":")[1]
    current_val = await get_setting(session, key)

    param_labels = {
        "institute_name": "Institutning rasmiy nomi",
        "department_name": "Kafedraning rasmiy nomi",
        "dekan_name": "Dekan (Kafedra rahbari) F.I.Sh.",
        "contact_phone": "Aloqa telefon raqami",
        "official_telegram": "Rasmiy Telegram username",
        "default_deadline_days": "Standart ko‘rib chiqish muddati (kun)"
    }
    label = param_labels.get(key, key)

    await state.update_data(editing_setting_key=key)
    await callback.message.edit_text(
        f"⚙️ <b>{label}</b>\n\n"
        f"Joriy qiymat: <code>{current_val}</code>\n\n"
        "Yangi qiymatni kiriting:\n(Bekor qilish uchun '❌ Bekor qilish' deb yozing)",
        parse_mode="HTML"
    )
    await state.set_state(AdminSettingsState.waiting_value)
    await callback.answer()


@router.message(AdminSettingsState.waiting_value, F.text)
async def save_setting_param(message: Message, state: FSMContext, session: AsyncSession):
    new_val = message.text.strip()
    data = await state.get_data()
    key = data.get("editing_setting_key")

    if not key:
        await state.clear()
        return

    user = await get_or_create_user(session, message.from_user.id)
    await set_setting(session, key, new_val)

    await log_audit(
        session=session,
        user_id=user.id,
        telegram_id=user.telegram_id,
        action="UPDATE_SETTING",
        target_type="SystemSetting",
        target_id=key,
        details=f"Sozlama yangilandi: {key} -> {new_val}"
    )

    await state.clear()
    buttons = [[InlineKeyboardButton(text="⚙️ Sozlamalarga qaytish", callback_data="admin_nav:settings")]]
    await message.answer(
        f"✅ <b>Sozlama muvaffaqiyatli yangilandi!</b>\n\nParametr: <code>{key}</code>\nYangi qiymat: <b>{new_val}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "set_toggle:appeals")
async def toggle_appeals_status(callback: CallbackQuery, session: AsyncSession):
    current = await get_setting(session, "appeals_enabled", "true")
    new_val = "false" if current.lower() == "true" else "true"
    await set_setting(session, "appeals_enabled", new_val)

    await callback.answer(f"Murojaatlar qabuli {'yoqildi' if new_val == 'true' else 'to‘xtatildi'}!", show_alert=True)
    await show_settings_main(callback, session)


# ==================== TOPICS MANAGEMENT ====================

@router.callback_query(F.data == "set_manage:topics")
async def manage_topics(callback: CallbackQuery, session: AsyncSession):
    topics = await get_all_topics(session)

    buttons = []
    text_lines = [
        "🗂 <b>MUROJAAT YO‘NALISHLARI (KAFEDRA BO‘YICHA)</b>\n",
        "Yo‘nalishni yoqish / o‘chirish uchun uning ustiga bosing:\n"
    ]

    for t in topics:
        status_icon = "🟢" if t.is_active else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {t.name}",
                callback_data=f"topic_toggle:{t.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="➕ Yangi yo‘nalish qo‘shish", callback_data="topic_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Sozlamalarga qaytish", callback_data="admin_nav:settings")])

    await callback.message.edit_text("\n".join(text_lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("topic_toggle:"))
async def toggle_topic(callback: CallbackQuery, session: AsyncSession):
    topic_id = int(callback.data.split(":")[1])
    topic = await toggle_topic_status(session, topic_id)
    if topic:
        status_word = "faollashtirildi" if topic.is_active else "o‘chirildi"
        await callback.answer(f"'{topic.name}' {status_word}!")
    await manage_topics(callback, session)


@router.callback_query(F.data == "topic_add")
async def add_topic_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ <b>YANGI MUROJAAT YO‘NALISHI QO‘SHISH</b>\n\n"
        "Yangi yo‘nalish nomini kiriting:\n"
        "<i>(Masalan: Magistratura dissertatsiyalari himoyasi)</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminSettingsState.waiting_topic_name)
    await callback.answer()


@router.message(AdminSettingsState.waiting_topic_name, F.text)
async def add_topic_finish(message: Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("Yo‘nalish nomi kamida 3 ta belgidan iborat bo‘lishi kerak:")
        return

    topic = await add_topic(session, name)
    await state.clear()

    buttons = [[InlineKeyboardButton(text="🗂 Yo‘nalishlar ro‘yxati", callback_data="set_manage:topics")]]
    await message.answer(
        f"✅ <b>'{topic.name}' yo‘nalishi muvaffaqiyatli qo‘shildi!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )


# ==================== DATABASE BACKUP ====================

@router.callback_query(F.data == "set_act:backup")
async def perform_database_backup(callback: CallbackQuery, bot: Bot):
    await callback.answer("Zaxira nusxasi olinmoqda...")
    os.makedirs("data/backups", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"data/backups/e_murojaat_backup_{timestamp}.db"

    # If SQLite file exists
    db_file = "data/e_murojaat.db"
    if os.path.exists(db_file):
        shutil.copy2(db_file, backup_file)
        doc = FSInputFile(backup_file, filename=f"e_murojaat_backup_{timestamp}.db")
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=doc,
            caption=f"💾 <b>Ma'lumotlar bazasining zaxira nusxasi ({timestamp}).</b>",
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("⚠️ PostgreSQL bazasi uchun zaxira nusxasi avtomatik pg_dump orqali serverda yuritiladi.")

