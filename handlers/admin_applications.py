import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import (
    User, Appeal, AppealStatus, UserRole, CorrespondenceMessage
)
from database.queries import (
    get_or_create_user, get_appeal_by_id, get_admin_appeals_paginated,
    search_appeals, update_appeal_status, get_all_staff_members,
    add_correspondence_message
)
from keyboards.admin import (
    get_appeals_pagination, get_appeal_card_actions,
    get_staff_selection_keyboard, get_deadline_keyboard
)
from states.admin import (
    AdminSearchState, AdminAssignState, AdminResponseState,
    AdminRejectState, AdminInternalNoteState, CorrespondenceState
)
from services.application_service import format_appeal_detail_view
from services.notification_service import (
    notify_status_change, notify_staff_assignment, notify_official_response
)
from utils.helpers import get_current_time, log_audit

logger = logging.getLogger(__name__)
router = Router(name="admin_applications_router")

PAGE_LIMIT = 5


# ==================== LIST & PAGINATION ====================

@router.callback_query(F.data.startswith("admin_nav:list:"))
async def list_admin_appeals(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    status_filter = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 1

    tg_id = callback.from_user.id
    user = await get_or_create_user(session, tg_id)

    # Check permission for confidential appeals
    allow_confidential = (
        (settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID) or
        user.role in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]
    )

    filter_param = None if status_filter == "ALL" else status_filter
    appeals, total = await get_admin_appeals_paginated(
        session=session,
        status=filter_param,
        allow_confidential=allow_confidential,
        page=page,
        limit=PAGE_LIMIT
    )

    filter_titles = {
        "ALL": "Barcha murojaatlar",
        "YANGI": "Yangi murojaatlar",
        "KORIB_CHIQILMOQDA": "Ko‘rib chiqilayotganlar",
        "PENDING_RESPONSE": "Javob kutilayotganlar",
        "HAL_QILINDI": "Hal qilinganlar",
        "RAD_ETILDI": "Rad etilganlar"
    }
    title = filter_titles.get(status_filter, status_filter)

    if total == 0:
        await callback.message.edit_text(
            f"📂 <b>{title.upper()}</b>\n\nUshbu toifada hozircha murojaatlar mavjud emas.",
            reply_markup=get_appeals_pagination([], 1, 0, PAGE_LIMIT, status_filter),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    kb = get_appeals_pagination(appeals, current_page=page, total_count=total, limit=PAGE_LIMIT, status_filter=status_filter)
    await callback.message.edit_text(
        f"📂 <b>{title.upper()} (Jami: {total} ta):</b>\n\n"
        "Batafsil ko‘rish va amallar bajarish uchun murojaatni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== VIEW DETAIL ====================

@router.callback_query(F.data.startswith("adm_view:"))
async def view_admin_appeal(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    appeal_id = int(parts[1])
    back_filter = parts[2] if len(parts) > 2 else "ALL"
    back_page = int(parts[3]) if len(parts) > 3 else 1

    tg_id = callback.from_user.id
    user = await get_or_create_user(session, tg_id)
    appeal = await get_appeal_by_id(session, appeal_id)

    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    # Check confidentiality security
    if appeal.is_confidential:
        is_allowed = (
            (settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID) or
            user.role in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]
        )
        if not is_allowed:
            await callback.answer("🔒 Ushbu murojaat MAXFIY. Faqat Dekan ko‘rishi mumkin!", show_alert=True)
            return

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=user.role, back_filter=back_filter, back_page=back_page)

    await callback.message.edit_text(detail_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ==================== ACTION: KO'RIB CHIQISHGA OLISH ====================

@router.callback_query(F.data.startswith("adm_act:take:"))
async def take_appeal_for_review(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    appeal_id = int(callback.data.split(":")[2])
    user = await get_or_create_user(session, callback.from_user.id)

    appeal = await update_appeal_status(
        session=session,
        appeal_id=appeal_id,
        new_status=AppealStatus.KORIB_CHIQILMOQDA.value,
        changed_by_id=user.id,
        comment=f"Murojaat {user.full_name} tomonidan ko‘rib chiqishga olindi."
    )
    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    await notify_status_change(bot, session, appeal, AppealStatus.KORIB_CHIQILMOQDA.value)

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=user.role)
    await callback.message.edit_text(detail_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("✅ Murojaat ko‘rib chiqishga olindi!")


# ==================== ACTION: MAS'ULGA BIRIKTIRISH ====================

@router.callback_query(F.data.startswith("adm_act:assign:"))
async def assign_staff_step1(callback: CallbackQuery, session: AsyncSession):
    appeal_id = int(callback.data.split(":")[2])
    staff_list = await get_all_staff_members(session)

    if not staff_list:
        await callback.answer("Tizimda tayinlangan xodimlar topilmadi!", show_alert=True)
        return

    kb = get_staff_selection_keyboard(staff_list, appeal_id)
    await callback.message.edit_text(
        "👤 <b>Murojaatni mas'ul xodimga biriktirish:</b>\n\n"
        "Quyidagi xodimlardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("staff_sel:"))
async def assign_staff_step2(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    appeal_id = int(parts[1])
    staff_id = int(parts[2])

    await state.update_data(assign_appeal_id=appeal_id, assign_staff_id=staff_id)
    await callback.message.edit_text(
        "⏱ <b>Ijro muddatini tanlang:</b>",
        reply_markup=get_deadline_keyboard(appeal_id, staff_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_dl:"))
async def assign_staff_step3(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    appeal_id = int(parts[1])
    staff_id = int(parts[2])
    days = int(parts[3])

    await state.update_data(assign_appeal_id=appeal_id, assign_staff_id=staff_id, assign_days=days)
    await callback.message.edit_text(
        f"Tanlangan muddat: <b>{days} kun</b>\n\n"
        "📝 <b>Xodim uchun topshiriq izohini / ko‘rsatmasini kiriting:</b>\n"
        "<i>(Masalan: Holatni joyida o‘rganib, xulosa taqdim etilsin)</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminAssignState.waiting_instruction)
    await callback.answer()


@router.message(AdminAssignState.waiting_instruction, F.text)
async def assign_staff_step4_finalize(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    instruction = message.text.strip()
    data = await state.get_data()
    appeal_id = data.get("assign_appeal_id")
    staff_id = data.get("assign_staff_id")
    days = data.get("assign_days", 5)

    current_user = await get_or_create_user(session, message.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)
    target_staff = (await session.execute(select(User).where(User.id == staff_id))).scalar_one_or_none()

    if not appeal or not target_staff:
        await message.answer("Xatolik: Murojaat yoki xodim topilmadi.")
        await state.clear()
        return

    # Update assignment
    deadline_date = datetime.now(timezone.utc) + timedelta(days=days)
    appeal.assigned_to_id = target_staff.id
    appeal.assigned_by_id = current_user.id
    appeal.assignment_note = instruction
    appeal.deadline = deadline_date
    appeal.status = AppealStatus.BIRIKTIRILDI.value
    appeal.updated_at = datetime.now(timezone.utc)

    # Log audit
    await log_audit(
        session=session,
        user_id=current_user.id,
        telegram_id=current_user.telegram_id,
        action="ASSIGN_STAFF",
        target_type="Appeal",
        target_id=str(appeal.id),
        details=f"Mas'ulga biriktirildi: {target_staff.full_name}, muddat: {days} kun. Topshiriq: {instruction}"
    )

    await session.commit()
    await state.clear()

    # Notify staff & applicant
    await notify_staff_assignment(bot, session, appeal, target_staff, current_user)
    await notify_status_change(bot, session, appeal, AppealStatus.BIRIKTIRILDI.value, comment=f"Murojaat kafedra mas'ul xodimi {target_staff.full_name}ga biriktirildi.")

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=current_user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=current_user.role)

    await message.answer(
        f"✅ <b>Murojaat muvaffaqiyatli biriktirildi!</b>\n"
        f"Mas'ul: <b>{target_staff.full_name}</b>\n"
        f"Muddat: <b>{days} kun</b>\n\n{detail_text}",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ==================== ACTION: JAVOB YUBORISH ====================

@router.callback_query(F.data.startswith("adm_act:respond:"))
async def respond_appeal_start(callback: CallbackQuery, state: FSMContext):
    appeal_id = int(callback.data.split(":")[2])
    await state.update_data(respond_appeal_id=appeal_id)

    await callback.message.edit_text(
        "📨 <b>MUROJAATGA RASMIY JAVOB YUBORISH</b>\n\n"
        "Murojaatchiga yuboriladigan rasmiy javob matnini kiriting:\n\n"
        "<i>Eslatma: Ushbu javob to‘g‘ridan-to‘g‘ri murojaatchining Telegramiga yuboriladi va murojaat holati '✅ Hal qilindi' deb belgilanadi.</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminResponseState.waiting_response_text)
    await callback.answer()


@router.message(AdminResponseState.waiting_response_text, F.text)
async def respond_appeal_finish(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    response_text = message.text.strip()
    data = await state.get_data()
    appeal_id = data.get("respond_appeal_id")

    current_user = await get_or_create_user(session, message.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)

    if not appeal:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return

    # Update appeal
    appeal.response_text = response_text
    appeal.responded_by_id = current_user.id
    appeal.responded_at = datetime.now(timezone.utc)
    appeal.completed_at = datetime.now(timezone.utc)
    appeal.status = AppealStatus.HAL_QILINDI.value
    appeal.updated_at = datetime.now(timezone.utc)

    # Add correspondence record
    await add_correspondence_message(
        session=session,
        appeal_id=appeal.id,
        sender_id=current_user.id,
        message_text=f"Rasmiy javob:\n{response_text}",
        is_internal=False
    )

    await log_audit(
        session=session,
        user_id=current_user.id,
        telegram_id=current_user.telegram_id,
        action="SEND_RESPONSE",
        target_type="Appeal",
        target_id=str(appeal.id),
        details=f"Rasmiy javob yuborildi: {response_text[:100]}..."
    )

    await session.commit()
    await state.clear()

    # Deliver response to applicant
    await notify_official_response(bot, appeal, response_text)

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=current_user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=current_user.role)

    await message.answer(
        f"✅ <b>Rasmiy javob murojaatchiga muvaffaqiyatli yuborildi!</b>\n\n{detail_text}",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ==================== ACTION: RAD ETISH ====================

@router.callback_query(F.data.startswith("adm_act:reject:"))
async def reject_appeal_start(callback: CallbackQuery, state: FSMContext):
    appeal_id = int(callback.data.split(":")[2])
    await state.update_data(reject_appeal_id=appeal_id)

    await callback.message.edit_text(
        "❌ <b>MUROJAATNI RAD ETISH</b>\n\n"
        "Murojaatni rad etish sababini batafsil kiriting:\n"
        "<i>(Rad etish sababi murojaatchiga rasman bildiriladi)</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminRejectState.waiting_rejection_reason)
    await callback.answer()


@router.message(AdminRejectState.waiting_rejection_reason, F.text)
async def reject_appeal_finish(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    reason = message.text.strip()
    data = await state.get_data()
    appeal_id = data.get("reject_appeal_id")

    current_user = await get_or_create_user(session, message.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)

    if not appeal:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return

    appeal.status = AppealStatus.RAD_ETILDI.value
    appeal.rejection_reason = reason
    appeal.completed_at = datetime.now(timezone.utc)
    appeal.updated_at = datetime.now(timezone.utc)

    await log_audit(
        session=session,
        user_id=current_user.id,
        telegram_id=current_user.telegram_id,
        action="REJECT_APPEAL",
        target_type="Appeal",
        target_id=str(appeal.id),
        details=f"Murojaat rad etildi. Sabab: {reason}"
    )

    await session.commit()
    await state.clear()

    # Notify applicant
    await notify_status_change(bot, session, appeal, AppealStatus.RAD_ETILDI.value, comment=reason)

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=current_user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=current_user.role)

    await message.answer(
        f"❌ <b>Murojaat rad etildi va murojaatchiga xabar yuborildi.</b>\n\n{detail_text}",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ==================== ACTION: HAL QILINDI ====================

@router.callback_query(F.data.startswith("adm_act:resolve:"))
async def resolve_appeal_quick(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    appeal_id = int(callback.data.split(":")[2])
    user = await get_or_create_user(session, callback.from_user.id)

    appeal = await update_appeal_status(
        session=session,
        appeal_id=appeal_id,
        new_status=AppealStatus.HAL_QILINDI.value,
        changed_by_id=user.id,
        comment=f"Murojaat {user.full_name} tomonidan ijobiy hal etildi deb belgilandi."
    )
    if not appeal:
        await callback.answer("Murojaat topilmadi!", show_alert=True)
        return

    await notify_status_change(bot, session, appeal, AppealStatus.HAL_QILINDI.value)

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=user.role)
    await callback.message.edit_text(detail_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer("✅ Murojaat ijobiy hal etildi deb belgilandi!")


# ==================== ACTION: ICHKI IZOH QOLDIRISH ====================

@router.callback_query(F.data.startswith("adm_act:note:"))
async def add_internal_note_start(callback: CallbackQuery, state: FSMContext):
    appeal_id = int(callback.data.split(":")[2])
    await state.update_data(note_appeal_id=appeal_id)

    await callback.message.edit_text(
        "📝 <b>ICHKI XIZMAT IZOHI QOLDIRISH</b>\n\n"
        "Xizmat izohini kiriting:\n"
        "<i>(Ushbu izoh faqat kafedra xodimlari va dekanatga ko‘rinadi, murojaatchiga KO‘RSATILMAYDI)</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminInternalNoteState.waiting_note)
    await callback.answer()


@router.message(AdminInternalNoteState.waiting_note, F.text)
async def add_internal_note_finish(message: Message, state: FSMContext, session: AsyncSession):
    note = message.text.strip()
    data = await state.get_data()
    appeal_id = data.get("note_appeal_id")

    user = await get_or_create_user(session, message.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)
    if not appeal:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return

    await add_correspondence_message(
        session=session,
        appeal_id=appeal.id,
        sender_id=user.id,
        message_text=f"[Ichki izoh]: {note}",
        is_internal=True
    )

    await log_audit(
        session=session,
        user_id=user.id,
        telegram_id=user.telegram_id,
        action="ADD_INTERNAL_NOTE",
        target_type="Appeal",
        target_id=str(appeal.id),
        details=note
    )

    await session.commit()
    await state.clear()

    detail_text = format_appeal_detail_view(appeal, is_staff=True, viewer_role=user.role)
    kb = get_appeal_card_actions(appeal, current_user_role=user.role)

    await message.answer(f"✅ <b>Ichki izoh muvaffaqiyatli saqlandi!</b>\n\n{detail_text}", reply_markup=kb, parse_mode="HTML")


# ==================== SEARCH APPEALS ====================

@router.callback_query(F.data == "admin_nav:search")
async def start_admin_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔎 <b>MUROJAATLARNI QIDIRISH</b>\n\n"
        "Qidiruv so‘zini kiriting:\n"
        "• Murojaat raqami (masalan: <code>AF-2026-000001</code>)\n"
        "• Murojaatchi F.I.Sh.\n"
        "• Telefon raqam\n"
        "• Murojaat mavzusi yoki mazmuni\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(AdminSearchState.waiting_query)
    await callback.answer()


@router.message(AdminSearchState.waiting_query, F.text)
async def process_admin_search(message: Message, state: FSMContext, session: AsyncSession):
    query = message.text.strip()
    user = await get_or_create_user(session, message.from_user.id)

    allow_confidential = (
        (settings.SUPER_ADMIN_ID and message.from_user.id == settings.SUPER_ADMIN_ID) or
        user.role in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]
    )

    results = await search_appeals(session, query, allow_confidential=allow_confidential)

    if not results:
        await message.answer(
            f"🔍 '<b>{query}</b>' bo‘yicha hech qanday murojaat topilmadi. Qaytadan qidirish uchun so‘z kiriting yoki '❌ Bekor qilish' deb yozing.",
            parse_mode="HTML"
        )
        return

    kb = get_appeals_pagination(results, current_page=1, total_count=len(results), limit=PAGE_LIMIT, status_filter="SEARCH")
    await message.answer(
        f"🔍 '<b>{query}</b>' so‘rovi bo‘yicha topilgan murojaatlar ({len(results)} ta):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

