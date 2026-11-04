import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserType(str, enum.Enum):
    TALABA = "TALABA"
    FUQARO = "FUQARO"
    OTA_ONA = "OTA_ONA"
    XODIM = "XODIM"
    BOSHQA = "BOSHQA"

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.TALABA: "🎓 Talaba",
            cls.FUQARO: "👤 Fuqaro",
            cls.OTA_ONA: "👨‍👩‍👧 Ota-ona",
            cls.XODIM: "🏢 Institut xodimi",
            cls.BOSHQA: "👥 Boshqa"
        }
        return labels.get(val, val)


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DEKAN = "DEKAN"
    ADMINISTRATOR = "ADMINISTRATOR"
    MASUL_XODIM = "MASUL_XODIM"
    USER = "USER"

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.SUPER_ADMIN: "👑 Super Administrator",
            cls.DEKAN: "🏛 Dekan",
            cls.ADMINISTRATOR: "⚙️ Administrator",
            cls.MASUL_XODIM: "👤 Mas'ul xodim",
            cls.USER: "👤 Murojaatchi"
        }
        return labels.get(val, val)


class AppealType(str, enum.Enum):
    ARIZA = "ARIZA"
    SHIKOYAT = "SHIKOYAT"
    TAKLIF = "TAKLIF"
    SAVOL = "SAVOL"
    YORDAM = "YORDAM"
    TASHAKKURNOMA = "TASHAKKURNOMA"
    BOSHQA = "BOSHQA"

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.ARIZA: "📄 Ariza",
            cls.SHIKOYAT: "⚠️ Shikoyat",
            cls.TAKLIF: "💡 Taklif",
            cls.SAVOL: "❓ Savol",
            cls.YORDAM: "🤝 Yordam so‘rash",
            cls.TASHAKKURNOMA: "🙏 Tashakkurnoma",
            cls.BOSHQA: "📌 Boshqa"
        }
        return labels.get(val, val)


class AppealStatus(str, enum.Enum):
    YANGI = "YANGI"
    ROYXATGA_OLINDI = "ROYXATGA_OLINDI"
    BIRIKTIRILDI = "BIRIKTIRILDI"
    KORIB_CHIQILMOQDA = "KORIB_CHIQILMOQDA"
    QOSHIMCHA_MALUMOT = "QOSHIMCHA_MALUMOT"
    YONALTIRILDI = "YONALTIRILDI"
    JAVOB_TAYYORLANMOQDA = "JAVOB_TAYYORLANMOQDA"
    HAL_QILINDI = "HAL_QILINDI"
    RAD_ETILDI = "RAD_ETILDI"
    ARXIVLANDI = "ARXIVLANDI"

    @classmethod
    def label(cls, val: str) -> str:
        labels = {
            cls.YANGI: "🆕 Yangi",
            cls.ROYXATGA_OLINDI: "📥 Ro‘yxatga olindi",
            cls.BIRIKTIRILDI: "👤 Mas'ulga biriktirildi",
            cls.KORIB_CHIQILMOQDA: "🔄 Ko‘rib chiqilmoqda",
            cls.QOSHIMCHA_MALUMOT: "📝 Qo‘shimcha ma'lumot so‘raldi",
            cls.YONALTIRILDI: "📤 Yo‘naltirildi",
            cls.JAVOB_TAYYORLANMOQDA: "📄 Javob tayyorlanmoqda",
            cls.HAL_QILINDI: "✅ Hal qilindi",
            cls.RAD_ETILDI: "❌ Rad etildi",
            cls.ARXIVLANDI: "📁 Arxivlandi"
        }
        return labels.get(val, val)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_type: Mapped[str] = mapped_column(String(50), default=UserType.TALABA.value)
    
    # Name fields
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Specific fields
    direction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Talaba: Ta'lim yo'nalishi
    course: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)          # Talaba: Kurs
    group_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Talaba: Guruh raqami
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)        # Fuqaro: Yashash hududi
    parent_relation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Ota-ona: Qarindoshlik darajasi
    child_group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # Ota-ona: Farzand guruhi
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Xodim/Boshqa: Tashkilot yoki faoliyat

    # Staff / admin fields
    role: Mapped[str] = mapped_column(String(50), default=UserRole.USER.value, nullable=False)
    staff_position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Lavozimi
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    appeals: Mapped[List["Appeal"]] = relationship("Appeal", back_populates="applicant", foreign_keys="Appeal.applicant_id")
    assigned_appeals: Mapped[List["Appeal"]] = relationship("Appeal", back_populates="assigned_to", foreign_keys="Appeal.assigned_to_id")


class AppealTopic(Base):
    __tablename__ = "appeal_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AppealSequence(Base):
    __tablename__ = "appeal_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Appeal(Base):
    __tablename__ = "appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appeal_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    applicant_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    appeal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default=AppealStatus.YANGI.value, nullable=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assignment
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    assignment_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resolution
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    applicant: Mapped["User"] = relationship("User", foreign_keys=[applicant_id], back_populates="appeals")
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_appeals")
    assigned_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by_id])
    responded_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[responded_by_id])
    
    files: Mapped[List["AppealFile"]] = relationship("AppealFile", back_populates="appeal", cascade="all, delete-orphan")
    status_history: Mapped[List["AppealStatusHistory"]] = relationship("AppealStatusHistory", back_populates="appeal", cascade="all, delete-orphan", order_by="AppealStatusHistory.created_at")
    messages: Mapped[List["CorrespondenceMessage"]] = relationship("CorrespondenceMessage", back_populates="appeal", cascade="all, delete-orphan", order_by="CorrespondenceMessage.created_at")


class AppealFile(Base):
    __tablename__ = "appeal_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(Integer, ForeignKey("appeals.id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_unique_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False) # document, photo, video
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    appeal: Mapped["Appeal"] = relationship("Appeal", back_populates="files")


class AppealStatusHistory(Base):
    __tablename__ = "appeal_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(Integer, ForeignKey("appeals.id", ondelete="CASCADE"), nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    appeal: Mapped["Appeal"] = relationship("Appeal", back_populates="status_history")
    changed_by: Mapped[Optional["User"]] = relationship("User")


class CorrespondenceMessage(Base):
    __tablename__ = "correspondence_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(Integer, ForeignKey("appeals.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # If True, only staff can see
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    appeal: Mapped["Appeal"] = relationship("Appeal", back_populates="messages")
    sender: Mapped["User"] = relationship("User")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user: Mapped[Optional["User"]] = relationship("User")
