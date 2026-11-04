import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserRole
from database.queries import get_or_create_user, get_appeal_by_number
from services.application_service import format_appeal_detail_view

logger = logging.getLogger(__name__)
router = Router(name="tracking_router")


class TrackingState(StatesGroup):
    waiting_appeal_number = State()


@router.message(F.text == "🔎 Murojaat holatini tekshirish")
async def start_tracking(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔎 <b>MUROJAAT HOLATINI TEKSHIRISH</b>\n\n"
        "Murojaatingiz holatini tekshirish uchun uning maxsus raqamini kiriting:\n"
        "<i>(Masalan: AF-2026-000001)</i>\n\n"
        "Bekor qilish uchun '❌ Bekor qilish' deb yozing.",
        parse_mode="HTML"
    )
    await state.set_state(TrackingState.waiting_appeal_number)


@router.message(TrackingState.waiting_appeal_number, F.text)
async def process_tracking_query(message: Message, state: FSMContext, session: AsyncSession):
    query = message.text.strip().upper()
    user = await get_or_create_user(session, message.from_user.id)

    appeal = await get_appeal_by_number(session, query)
    if not appeal:
        await message.answer(
            f"❌ <b>{query}</b> raqamli murojaat tizimda topilmadi!\n"
            "Iltimos, murojaat raqami to‘g‘ri kiritilganligini tekshirib, qaytadan urinib ko‘ring.",
            parse_mode="HTML"
        )
        return

    # Check access permission: applicant or staff member
    is_staff = user.role in [
        UserRole.SUPER_ADMIN.value,
        UserRole.DEKAN.value,
        UserRole.ADMINISTRATOR.value,
        UserRole.MASUL_XODIM.value
    ]

    if appeal.applicant_id != user.id and not is_staff:
        # User is not allowed to inspect other people's appeals
        await message.answer("❌ Bu murojaat Sizning hisobingizga tegishli emas yoki unga kirish huquqi cheklangan.")
        await state.clear()
        return

    text = format_appeal_detail_view(appeal, is_staff=is_staff, viewer_role=user.role)
    await message.answer(text, parse_mode="HTML")
    await state.clear()

