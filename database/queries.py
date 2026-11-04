from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, select, or_, and_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User, UserRole, UserType, Appeal, AppealFile, AppealStatus, 
    AppealStatusHistory, AppealTopic, CorrespondenceMessage, SystemSetting, AuditLog
)
from utils.helpers import get_current_time, log_audit


# ==================== USER QUERIES ====================

async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    stmt = select(User).where(User.telegram_id == tg_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: Optional[str] = None,
    full_name: str = "Foydalanuvchi"
) -> User:
    user = await get_user_by_tg_id(session, tg_id)
    if not user:
        user = User(
            telegram_id=tg_id,
            username=username,
            full_name=full_name,
            phone="",
            user_type=UserType.TALABA.value,
            role=UserRole.USER.value,
            is_active=True,
            is_registered=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        if username and user.username != username:
            user.username = username
            await session.commit()
    return user


async def get_admins_for_notification(session: AsyncSession, is_confidential: bool = False) -> List[User]:
    """Returns list of administrators who should receive new appeal notification."""
    if is_confidential:
        # Only Super Admin and Dekan
        stmt = select(User).where(
            User.role.in_([UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value]),
            User.is_active == True
        )
    else:
        # Super Admin, Dekan, Administrator
        stmt = select(User).where(
            User.role.in_([UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value, UserRole.ADMINISTRATOR.value]),
            User.is_active == True
        )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_all_staff_members(session: AsyncSession) -> List[User]:
    """Returns all staff: Super Admin, Dekan, Administrator, Mas'ul xodim."""
    stmt = select(User).where(
        User.role.in_([
            UserRole.SUPER_ADMIN.value,
            UserRole.DEKAN.value,
            UserRole.ADMINISTRATOR.value,
            UserRole.MASUL_XODIM.value
        ]),
        User.is_active == True
    ).order_by(User.full_name)
    res = await session.execute(stmt)
    return list(res.scalars().all())


# ==================== TOPIC QUERIES ====================

async def get_active_topics(session: AsyncSession) -> List[AppealTopic]:
    stmt = select(AppealTopic).where(AppealTopic.is_active == True).order_by(AppealTopic.order_num, AppealTopic.name)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_all_topics(session: AsyncSession) -> List[AppealTopic]:
    stmt = select(AppealTopic).order_by(AppealTopic.order_num, AppealTopic.name)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def add_topic(session: AsyncSession, name: str) -> AppealTopic:
    topic = AppealTopic(name=name.strip(), is_active=True)
    session.add(topic)
    await session.commit()
    await session.refresh(topic)
    return topic


async def toggle_topic_status(session: AsyncSession, topic_id: int) -> Optional[AppealTopic]:
    stmt = select(AppealTopic).where(AppealTopic.id == topic_id)
    res = await session.execute(stmt)
    topic = res.scalar_one_or_none()
    if topic:
        topic.is_active = not topic.is_active
        await session.commit()
        await session.refresh(topic)
    return topic


# ==================== APPEAL QUERIES ====================

async def get_appeal_by_id(session: AsyncSession, appeal_id: int) -> Optional[Appeal]:
    stmt = (
        select(Appeal)
        .where(Appeal.id == appeal_id)
        .options(
            selectinload(Appeal.applicant),
            selectinload(Appeal.assigned_to),
            selectinload(Appeal.assigned_by),
            selectinload(Appeal.responded_by),
            selectinload(Appeal.files),
            selectinload(Appeal.status_history).selectinload(AppealStatusHistory.changed_by),
            selectinload(Appeal.messages).selectinload(CorrespondenceMessage.sender),
        )
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_appeal_by_number(session: AsyncSession, appeal_number: str) -> Optional[Appeal]:
    stmt = (
        select(Appeal)
        .where(func.upper(Appeal.appeal_number) == appeal_number.strip().upper())
        .options(
            selectinload(Appeal.applicant),
            selectinload(Appeal.assigned_to),
            selectinload(Appeal.files),
            selectinload(Appeal.status_history),
            selectinload(Appeal.messages),
        )
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_user_appeals_paginated(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    limit: int = 5
) -> Tuple[List[Appeal], int]:
    offset = (page - 1) * limit
    
    count_stmt = select(func.count(Appeal.id)).where(Appeal.applicant_id == user_id)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(Appeal)
        .where(Appeal.applicant_id == user_id)
        .order_by(desc(Appeal.created_at))
        .offset(offset)
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all()), total


async def get_admin_appeals_paginated(
    session: AsyncSession,
    status: Optional[str] = None,
    allow_confidential: bool = True,
    assigned_to_id: Optional[int] = None,
    page: int = 1,
    limit: int = 5
) -> Tuple[List[Appeal], int]:
    offset = (page - 1) * limit
    
    conditions = []
    if status:
        if status == "PENDING_RESPONSE":
            conditions.append(Appeal.status.in_([
                AppealStatus.KORIB_CHIQILMOQDA.value,
                AppealStatus.JAVOB_TAYYORLANMOQDA.value,
                AppealStatus.BIRIKTIRILDI.value,
                AppealStatus.QOSHIMCHA_MALUMOT.value
            ]))
        else:
            conditions.append(Appeal.status == status)

    if not allow_confidential:
        conditions.append(Appeal.is_confidential == False)

    if assigned_to_id is not None:
        conditions.append(Appeal.assigned_to_id == assigned_to_id)

    count_stmt = select(func.count(Appeal.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = select(Appeal).options(
        selectinload(Appeal.applicant),
        selectinload(Appeal.assigned_to)
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))
        
    stmt = stmt.order_by(desc(Appeal.created_at)).offset(offset).limit(limit)
    res = await session.execute(stmt)
    return list(res.scalars().all()), total


async def search_appeals(
    session: AsyncSession,
    query: str,
    allow_confidential: bool = True
) -> List[Appeal]:
    clean_query = query.strip()
    conditions = [
        or_(
            Appeal.appeal_number.ilike(f"%{clean_query}%"),
            Appeal.title.ilike(f"%{clean_query}%"),
            Appeal.description.ilike(f"%{clean_query}%"),
            User.full_name.ilike(f"%{clean_query}%"),
            User.phone.ilike(f"%{clean_query}%")
        )
    ]
    if not allow_confidential:
        conditions.append(Appeal.is_confidential == False)

    stmt = (
        select(Appeal)
        .join(User, Appeal.applicant_id == User.id)
        .where(and_(*conditions))
        .options(selectinload(Appeal.applicant))
        .order_by(desc(Appeal.created_at))
        .limit(20)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


# ==================== STATUS & WORKFLOW ====================

async def update_appeal_status(
    session: AsyncSession,
    appeal_id: int,
    new_status: str,
    changed_by_id: Optional[int] = None,
    comment: Optional[str] = None
) -> Optional[Appeal]:
    appeal = await get_appeal_by_id(session, appeal_id)
    if not appeal:
        return None

    old_status = appeal.status
    appeal.status = new_status
    appeal.updated_at = datetime.now(timezone.utc)

    if new_status in [AppealStatus.HAL_QILINDI.value, AppealStatus.RAD_ETILDI.value]:
        appeal.completed_at = datetime.now(timezone.utc)

    # History record
    history = AppealStatusHistory(
        appeal_id=appeal.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=changed_by_id,
        comment=comment
    )
    session.add(history)
    
    await log_audit(
        session=session,
        user_id=changed_by_id,
        telegram_id=None,
        action="STATUS_CHANGE",
        target_type="Appeal",
        target_id=str(appeal.id),
        details=f"Status o'zgartirildi: {old_status} -> {new_status}. Izoh: {comment}"
    )

    await session.commit()
    await session.refresh(appeal)
    return appeal


# ==================== CORRESPONDENCE ====================

async def add_correspondence_message(
    session: AsyncSession,
    appeal_id: int,
    sender_id: int,
    message_text: Optional[str] = None,
    file_id: Optional[str] = None,
    file_type: Optional[str] = None,
    file_name: Optional[str] = None,
    is_internal: bool = False
) -> CorrespondenceMessage:
    msg = CorrespondenceMessage(
        appeal_id=appeal_id,
        sender_id=sender_id,
        message_text=message_text,
        file_id=file_id,
        file_type=file_type,
        file_name=file_name,
        is_internal=is_internal
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


# ==================== STATISTICS ====================

async def get_dashboard_statistics(
    session: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    time_filter = []
    if start_date:
        time_filter.append(Appeal.created_at >= start_date)
    if end_date:
        time_filter.append(Appeal.created_at <= end_date)

    base_where = and_(*time_filter) if time_filter else True

    # Total
    total_q = await session.execute(select(func.count(Appeal.id)).where(base_where))
    total_count = total_q.scalar_one()

    # Status counts
    yangi_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.status == AppealStatus.YANGI.value)
    )
    yangi_count = yangi_q.scalar_one()

    korib_q = await session.execute(
        select(func.count(Appeal.id)).where(
            base_where,
            Appeal.status.in_([
                AppealStatus.KORIB_CHIQILMOQDA.value,
                AppealStatus.BIRIKTIRILDI.value,
                AppealStatus.QOSHIMCHA_MALUMOT.value,
                AppealStatus.JAVOB_TAYYORLANMOQDA.value
            ])
        )
    )
    korib_count = korib_q.scalar_one()

    hal_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.status == AppealStatus.HAL_QILINDI.value)
    )
    hal_count = hal_q.scalar_one()

    rad_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.status == AppealStatus.RAD_ETILDI.value)
    )
    rad_count = rad_q.scalar_one()

    # Overdue count (deadline passed, not completed)
    now = datetime.now(timezone.utc)
    overdue_q = await session.execute(
        select(func.count(Appeal.id)).where(
            base_where,
            Appeal.deadline < now,
            Appeal.status.notin_([AppealStatus.HAL_QILINDI.value, AppealStatus.RAD_ETILDI.value, AppealStatus.ARXIVLANDI.value])
        )
    )
    overdue_count = overdue_q.scalar_one()

    # By applicant type
    talaba_q = await session.execute(
        select(func.count(Appeal.id))
        .join(User, Appeal.applicant_id == User.id)
        .where(base_where, User.user_type == UserType.TALABA.value)
    )
    talaba_count = talaba_q.scalar_one()

    fuqaro_q = await session.execute(
        select(func.count(Appeal.id))
        .join(User, Appeal.applicant_id == User.id)
        .where(base_where, User.user_type == UserType.FUQARO.value)
    )
    fuqaro_count = fuqaro_q.scalar_one()

    # By appeal types (ariza, shikoyat, taklif, savol)
    ariza_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.appeal_type == "ARIZA")
    )
    ariza_count = ariza_q.scalar_one()

    shikoyat_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.appeal_type == "SHIKOYAT")
    )
    shikoyat_count = shikoyat_q.scalar_one()

    taklif_q = await session.execute(
        select(func.count(Appeal.id)).where(base_where, Appeal.appeal_type == "TAKLIF")
    )
    taklif_count = taklif_q.scalar_one()

    return {
        "total": total_count,
        "yangi": yangi_count,
        "korib_chiqilmoqda": korib_count,
        "hal_qilindi": hal_count,
        "rad_etildi": rad_count,
        "overdue": overdue_count,
        "talabalar": talaba_count,
        "fuqarolar": fuqaro_count,
        "arizalar": ariza_count,
        "shikoyatlar": shikoyat_count,
        "takliflar": taklif_count,
    }
