import os
import re
from datetime import datetime
from typing import Optional, Tuple
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import AuditLog, SystemSetting


def get_current_time() -> datetime:
    tz = pytz.timezone(settings.TIMEZONE)
    return datetime.now(tz)


def format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return "Mavjud emas"
    try:
        tz = pytz.timezone(settings.TIMEZONE)
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = pytz.utc.localize(dt)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return dt.strftime("%d.%m.%Y %H:%M")


def format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "Mavjud emas"
    try:
        tz = pytz.timezone(settings.TIMEZONE)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime("%d.%m.%Y")
    except Exception:
        return dt.strftime("%d.%m.%Y")


def normalize_phone(phone: str) -> Optional[str]:
    """Validates and normalizes phone number to format +998901234567."""
    clean = re.sub(r"[^\d+]", "", phone.strip())
    if clean.startswith("998") and len(clean) == 12:
        return f"+{clean}"
    if clean.startswith("+998") and len(clean) == 13:
        return clean
    if len(clean) == 9 and clean.isdigit():
        return f"+998{clean}"
    if clean.startswith("8") and len(clean) == 10:
        return f"+998{clean[1:]}"
    # If general international format
    if clean.startswith("+") and 10 <= len(clean) <= 15:
        return clean
    return None


def validate_file(file_name: Optional[str], file_size: Optional[int]) -> Tuple[bool, str]:
    """Validates file extension and size."""
    if file_size and file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"Fayl hajmi ruxsat etilgan maksimal hajmdan ({settings.MAX_FILE_SIZE_MB} MB) oshib ketdi!"
    
    if file_name:
        ext = os.path.splitext(file_name)[1].lower()
        if ext and ext not in settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_EXTENSIONS)
            return False, f"Ruxsat etilmagan fayl formati ({ext}). Ruxsat etilganlar: {allowed}"

    return True, ""


async def log_audit(
    session: AsyncSession,
    user_id: Optional[int],
    telegram_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None
) -> None:
    """Writes an entry into audit log table."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            telegram_id=telegram_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            details=details
        )
        session.add(log_entry)
        await session.flush()
    except Exception as e:
        # Audit log failure should not break the main transaction if handled
        pass


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    """Retrieves a system setting by key."""
    res = await session.execute(select(SystemSetting.value).where(SystemSetting.key == key))
    val = res.scalar_one_or_none()
    return val if val is not None else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    """Updates or creates a system setting."""
    res = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = res.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        session.add(SystemSetting(key=key, value=value))
    await session.commit()

