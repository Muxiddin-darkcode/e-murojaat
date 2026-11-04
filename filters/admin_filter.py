from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import User, UserRole


class IsStaffFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], session: AsyncSession) -> bool:
        tg_id = event.from_user.id
        if (settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID) or (settings.DEKAN_ID and tg_id == settings.DEKAN_ID):
            return True
        stmt = select(User.role, User.is_active).where(User.telegram_id == tg_id)
        res = await session.execute(stmt)
        row = res.first()
        if not row or not row[1]:  # not exists or not active
            return False
        return row[0] in [
            UserRole.SUPER_ADMIN.value,
            UserRole.DEKAN.value,
            UserRole.ADMINISTRATOR.value,
            UserRole.MASUL_XODIM.value
        ]


class IsAdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], session: AsyncSession) -> bool:
        tg_id = event.from_user.id
        if (settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID) or (settings.DEKAN_ID and tg_id == settings.DEKAN_ID):
            return True
        stmt = select(User.role, User.is_active).where(User.telegram_id == tg_id)
        res = await session.execute(stmt)
        row = res.first()
        if not row or not row[1]:
            return False
        return row[0] in [
            UserRole.SUPER_ADMIN.value,
            UserRole.DEKAN.value,
            UserRole.ADMINISTRATOR.value
        ]


class IsSuperAdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], session: AsyncSession) -> bool:
        tg_id = event.from_user.id
        if settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID:
            return True
        stmt = select(User.role, User.is_active).where(User.telegram_id == tg_id)
        res = await session.execute(stmt)
        row = res.first()
        if not row or not row[1]:
            return False
        return row[0] == UserRole.SUPER_ADMIN.value


class IsDekanFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], session: AsyncSession) -> bool:
        tg_id = event.from_user.id
        if (settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID) or (settings.DEKAN_ID and tg_id == settings.DEKAN_ID):
            return True
        stmt = select(User.role, User.is_active).where(User.telegram_id == tg_id)
        res = await session.execute(stmt)
        row = res.first()
        if not row or not row[1]:
            return False
        return row[0] in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]
        tg_id = event.from_user.id
        if settings.SUPER_ADMIN_ID and tg_id == settings.SUPER_ADMIN_ID:
            return True
        stmt = select(User.role, User.is_active).where(User.telegram_id == tg_id)
        res = await session.execute(stmt)
        row = res.first()
        if not row or not row[1]:
            return False
        return row[0] in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]

