import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database.models import User, Appeal, CorrespondenceMessage, UserRole
from database.queries import (
    get_or_create_user, get_appeal_by_id, add_correspondence_message,
    get_user_appeals_paginated
)
from keyboards.main import get_main_menu_keyboard
from states.admin import CorrespondenceState
from utils.helpers import format_datetime, validate_file

logger = logging.getLogger(__name__)
router = Router(name="correspondence_router")


@router.message(F.text.contains("Dekanat bilan yozishmalar"))
async def show_correspondence_appeals(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await get_or_create_user(session, message.from_user.id)
    if not user.is_registered:
        await message.answer("Siz hali ro‘yxatdan o‘tmagansiz. /start orqali ro‘yxatdan o‘ting.")
        return

    appeals, total = await get_user_appeals_paginated(session, user_id=user.id, page=1, limit=10)
    if not appeals:
        await message.answer("Sizda hali murojaatlar mavjud emas. Avval '📝 Murojaat yuborish' orqali murojaat yo‘llang.")
        return

    try:
        temp = await message.answer("💬", reply_markup=ReplyKeyboardRemove())
        await temp.delete()
    except Exception:
        pass

    buttons = []
    for app in appeals:
        buttons.append([
            InlineKeyboardButton(
                text=f"💬 {app.appeal_number} - {app.title[:25]}",
                callback_data=f"user_chat:{app.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Yopish", callback_data="user_app_close")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "💬 <b>DEKANAT BILAN YOZISHMALAR</b>\n\n"
        "Qaysi murojaatingiz yuzasidan dekanat bilan muloqot qilmoqchisiz? Quyidagilardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("user_chat:"))
async def open_user_chat(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    appeal_id = int(callback.data.split(":")[1])
    user = await get_or_create_user(session, callback.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)

    if not appeal or appeal.applicant_id != user.id:
        await callback.answer("Murojaat topilmadi yoki unga kirish huquqingiz yo‘q!", show_alert=True)
        return

    # Fetch existing correspondence messages (non-internal only!)
    stmt = (
        select(CorrespondenceMessage)
        .where(
            CorrespondenceMessage.appeal_id == appeal_id,
            CorrespondenceMessage.is_internal == False
        )
        .order_by(CorrespondenceMessage.created_at)
    )
    res = await session.execute(stmt)
    messages = list(res.scalars().all())

    history_lines = [
        f"💬 <b>{appeal.appeal_number} RAQAMLI MUROJAAT BO‘YICHA YOZISHMALAR</b>\n",
        f"<b>Mavzu:</b> {appeal.title}\n"
    ]

    if messages:
        history_lines.append("<b>— Xabarlar tarixi —</b>")
        for m in messages:
            sender_tag = "Siz" if m.sender_id == user.id else "🏛 Dekanat"
            file_tag = f" 📎 [Fayl: {m.file_name or m.file_type}]" if m.file_id else ""
            msg_body = m.message_text or ""
            history_lines.append(f"<b>[{format_datetime(m.created_at)}] {sender_tag}:</b>\n{msg_body}{file_tag}\n")
    else:
        history_lines.append("<i>Ushbu murojaat bo‘yicha hali yozishmalar mavjud emas.</i>\n")

    history_lines.append("Dekanatga yuboriladigan xabaringizni yozing yoki fayl biriktiring:\n(Bekor qilish uchun '❌ Bekor qilish' deb yozing)")

    await state.update_data(active_chat_appeal_id=appeal.id)
    await callback.message.edit_text("\n".join(history_lines), parse_mode="HTML")
    await state.set_state(CorrespondenceState.waiting_message)
    await callback.answer()


@router.message(CorrespondenceState.waiting_message, F.text | F.document | F.photo)
async def process_user_chat_message(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    appeal_id = data.get("active_chat_appeal_id")
    if not appeal_id:
        await state.clear()
        return

    user = await get_or_create_user(session, message.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)
    if not appeal:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return

    msg_text = message.text
    file_id = None
    file_type = None
    file_name = None

    if message.document:
        doc = message.document
        valid, err = validate_file(doc.file_name, doc.file_size)
        if not valid:
            await message.answer(f"⚠️ {err}")
            return
        file_id = doc.file_id
        file_type = "document"
        file_name = doc.file_name
        msg_text = message.caption or "Fayl biriktirildi"
    elif message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_type = "photo"
        file_name = f"photo_{photo.file_unique_id}.jpg"
        msg_text = message.caption or "Rasm biriktirildi"

    if not msg_text and not file_id:
        await message.answer("Iltimos, xabar matni yoki fayl yuboring:")
        return

    # Save to DB
    await add_correspondence_message(
        session=session,
        appeal_id=appeal.id,
        sender_id=user.id,
        message_text=msg_text,
        file_id=file_id,
        file_type=file_type,
        file_name=file_name,
        is_internal=False
    )

    await state.clear()
    is_staff = user.role in [
        UserRole.SUPER_ADMIN.value,
        UserRole.DEKAN.value,
        UserRole.ADMINISTRATOR.value,
        UserRole.MASUL_XODIM.value
    ]
    await message.answer(
        f"✅ <b>Xabaringiz {appeal.appeal_number} raqamli murojaat bo‘yicha dekanatga yetkazildi!</b>",
        reply_markup=get_main_menu_keyboard(is_staff=is_staff),
        parse_mode="HTML"
    )

    # Notify assigned staff or dekan
    target_users = []
    if appeal.assigned_to and appeal.assigned_to.telegram_id:
        target_users.append(appeal.assigned_to)

    notification_text = (
        f"💬 <b>MUROJAATCHIDAN YANGI XABAR</b>\n\n"
        f"<b>Murojaat:</b> <code>{appeal.appeal_number}</code>\n"
        f"<b>Murojaatchi:</b> {user.full_name}\n"
        f"<b>Xabar:</b>\n{msg_text}\n"
    )

    for target in target_users:
        try:
            await bot.send_message(target.telegram_id, notification_text, parse_mode="HTML")
            if file_id:
                if file_type == "document":
                    await bot.send_document(target.telegram_id, document=file_id)
                elif file_type == "photo":
                    await bot.send_photo(target.telegram_id, photo=file_id)
        except Exception as e:
            logger.warning(f"Could not forward correspondence message to staff {target.telegram_id}: {e}")

