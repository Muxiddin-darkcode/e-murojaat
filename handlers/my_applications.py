import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import (
    get_or_create_user, get_user_appeals_paginated, get_appeal_by_id
)
from keyboards.staff import get_user_appeals_pagination, get_user_appeal_detail_keyboard
from services.application_service import format_appeal_detail_view

logger = logging.getLogger(__name__)
router = Router(name="my_applications_router")

PAGE_LIMIT = 5


@router.message(F.text == "📂 Mening murojaatlarim")
async def show_my_appeals(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id)
    if not user.is_registered:
        await message.answer("Siz hali ro‘yxatdan o‘tmagansiz. /start orqali ro‘yxatdan o‘ting.")
        return

    appeals, total = await get_user_appeals_paginated(
        session=session,
        user_id=user.id,
        page=1,
        limit=PAGE_LIMIT
    )

    if not appeals:
        await message.answer("Sizda hali yuborilgan murojaatlar mavjud emas. Yangi murojaat yuborish uchun '📝 Murojaat yuborish' tugmasini bosing.")
        return

    kb = get_user_appeals_pagination(appeals, current_page=1, total_count=total, limit=PAGE_LIMIT)
    await message.answer(
        f"📂 <b>SIZNING MUROJAATLARINGIZ (Jami: {total} ta):</b>\n\n"
        "Murojaat tafsilotlarini ko‘rish uchun quyidagi ro‘yxatdan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("user_app_page:"))
async def paginate_user_appeals(callback: CallbackQuery, session: AsyncSession):
    page = int(callback.data.split(":")[1])
    user = await get_or_create_user(session, callback.from_user.id)

    appeals, total = await get_user_appeals_paginated(
        session=session,
        user_id=user.id,
        page=page,
        limit=PAGE_LIMIT
    )

    kb = get_user_appeals_pagination(appeals, current_page=page, total_count=total, limit=PAGE_LIMIT)
    try:
        await callback.message.edit_text(
            f"📂 <b>SIZNING MUROJAATLARINGIZ (Jami: {total} ta):</b>\n\n"
            "Murojaat tafsilotlarini ko‘rish uchun quyidagi ro‘yxatdan birini tanlang:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("user_app_view:"))
async def view_user_appeal_detail(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    appeal_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1

    user = await get_or_create_user(session, callback.from_user.id)
    appeal = await get_appeal_by_id(session, appeal_id)

    # Security check: User can only view their own appeals!
    if not appeal or appeal.applicant_id != user.id:
        await callback.answer("Murojaat topilmadi yoki unga kirish huquqiga ega emassiz!", show_alert=True)
        return

    detail_text = format_appeal_detail_view(appeal, is_staff=False, viewer_role="USER")
    kb = get_user_appeal_detail_keyboard(appeal_id=appeal.id, page=page)

    await callback.message.edit_text(detail_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "user_app_close")
async def close_user_appeals_view(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()
