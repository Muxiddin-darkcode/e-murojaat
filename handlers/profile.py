import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserType
from database.queries import get_or_create_user
from keyboards.user import get_profile_actions_keyboard, get_profile_edit_fields_keyboard
from states.registration import ProfileEditState
from utils.helpers import format_datetime, normalize_phone, log_audit

logger = logging.getLogger(__name__)
router = Router(name="profile_router")


def format_user_profile(user: User) -> str:
    text = (
        "👤 <b>SIZNING PROFILINGIZ</b>\n\n"
        f"<b>Toifa:</b> {UserType.label(user.user_type)}\n"
        f"<b>F.I.Sh:</b> {user.full_name}\n"
        f"<b>Telefon:</b> {user.phone or 'Kiritilmagan'}\n"
        f"<b>Telegram ID:</b> <code>{user.telegram_id}</code>\n"
    )

    if user.user_type == UserType.TALABA.value:
        text += (
            f"<b>Ta'lim yo‘nalishi:</b> {user.direction or '-'}\n"
            f"<b>Kurs:</b> {user.course or '-'}-kurs\n"
            f"<b>Guruh:</b> {user.group_number or '-'}\n"
        )
    elif user.user_type == UserType.FUQARO.value:
        text += f"<b>Yashash hududi:</b> {user.region or '-'}\n"
    elif user.user_type == UserType.OTA_ONA.value:
        text += (
            f"<b>Qarindoshlik:</b> {user.parent_relation or '-'}\n"
            f"<b>Farzand guruhi:</b> {user.child_group or '-'}\n"
        )
    else:
        text += f"<b>Tashkilot / Faoliyat:</b> {user.organization or '-'}\n"

    text += f"\n<b>Ro‘yxatdan o‘tgan sana:</b> {format_datetime(user.created_at)}"
    return text


@router.message(F.text == "👤 Mening profilim")
async def show_profile(message: Message, session: AsyncSession):
    user = await get_or_create_user(session, message.from_user.id)
    if not user.is_registered:
        await message.answer("Siz hali ro‘yxatdan o‘tmagansiz. /start buyrug‘ini yuboring.")
        return

    text = format_user_profile(user)
    await message.answer(text, reply_markup=get_profile_actions_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "profile:refresh")
async def refresh_profile(callback: CallbackQuery, session: AsyncSession):
    user = await get_or_create_user(session, callback.from_user.id)
    text = format_user_profile(user)
    try:
        await callback.message.edit_text(text, reply_markup=get_profile_actions_keyboard(), parse_mode="HTML")
    except Exception:
        pass
    await callback.answer("Profil yangilandi")


@router.callback_query(F.data == "profile:edit")
async def edit_profile_menu(callback: CallbackQuery, session: AsyncSession):
    user = await get_or_create_user(session, callback.from_user.id)
    kb = get_profile_edit_fields_keyboard(user.user_type)
    await callback.message.edit_text("Qaysi ma'lumotni tahrirlamoqchisiz? Tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "profile:back")
async def profile_back(callback: CallbackQuery, session: AsyncSession):
    user = await get_or_create_user(session, callback.from_user.id)
    text = format_user_profile(user)
    await callback.message.edit_text(text, reply_markup=get_profile_actions_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def on_field_selected(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    field_names = {
        "full_name": "yangi F.I.Sh.ingizni",
        "phone": "yangi telefon raqamingizni (+998901234567 formatida)",
        "direction": "yangi ta'lim yo‘nalishingizni",
        "course": "yangi kursingizni (1, 2, 3, 4)",
        "group_number": "yangi guruh raqamingizni",
        "region": "yangi yashash hududingizni",
        "parent_relation": "yangi qarindoshlik darajangizni (Ona, Ota, Vasiy)",
        "child_group": "farzandingizning yangi guruh raqamini",
        "organization": "yangi tashkilotingiz yoki lavozimingizni"
    }
    prompt = field_names.get(field, "yangi qiymatni")
    await state.update_data(editing_field=field)
    await callback.message.edit_text(f"Iltimos, {prompt} kiriting:\n(Bekor qilish uchun '❌ Bekor qilish' deb yozing)")
    await state.set_state(ProfileEditState.waiting_value)
    await callback.answer()


@router.message(ProfileEditState.waiting_value)
async def process_field_value(message: Message, state: FSMContext, session: AsyncSession):
    val = message.text.strip()
    data = await state.get_data()
    field = data.get("editing_field")
    user = await get_or_create_user(session, message.from_user.id)

    if field == "phone":
        norm = normalize_phone(val)
        if not norm:
            await message.answer("Telefon raqami noto‘g‘ri formatda (+998901234567). Qaytadan kiriting:")
            return
        user.phone = norm
    elif field == "course":
        if not val.isdigit() or int(val) not in [1, 2, 3, 4, 5]:
            await message.answer("Kurs raqami 1 dan 5 gacha bo‘lgan son bo‘lishi kerak. Qaytadan kiriting:")
            return
        user.course = int(val)
    elif field == "full_name":
        if len(val) < 4:
            await message.answer("F.I.Sh. to‘liq kiritilishi kerak. Qaytadan kiriting:")
            return
        user.full_name = val
    elif hasattr(user, field):
        setattr(user, field, val)

    await log_audit(
        session=session,
        user_id=user.id,
        telegram_id=user.telegram_id,
        action="UPDATE_PROFILE",
        target_type="User",
        target_id=str(user.id),
        details=f"Profil maydoni yangilandi: {field} -> {val}"
    )

    await session.commit()
    await state.clear()
    await message.answer(f"✅ Ma'lumot muvaffaqiyatli saqlandi!\n\n{format_user_profile(user)}", reply_markup=get_profile_actions_keyboard(), parse_mode="HTML")
