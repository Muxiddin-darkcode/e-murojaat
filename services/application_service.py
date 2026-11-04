from typing import Any, Dict, List
from database.models import Appeal, AppealStatus, UserRole, UserType, AppealType
from utils.helpers import format_datetime


def format_appeal_confirmation(data: Dict[str, Any]) -> str:
    """Formats appeal data before final submission (Step 7)."""
    app_type_label = AppealType.label(data.get("appeal_type", ""))
    topic_name = data.get("topic_name", "")
    title = data.get("title", "")
    description = data.get("description", "")
    confidential = "🔒 Maxfiy (Faqat Dekan)" if data.get("is_confidential") else "🌐 Oddiy"
    files = data.get("files", [])
    files_text = f"{len(files)} ta fayl biriktirildi" if files else "Fayl biriktirilmadi"

    text = (
        "📋 <b>MUROJAATNI YAKUNIY TEKSHIRISH VA TASDIQLASH</b>\n\n"
        f"<b>Murojaat turi:</b> {app_type_label}\n"
        f"<b>Fakultet yo‘nalishi:</b> {topic_name}\n"
        f"<b>Mavzu:</b> {title}\n\n"
        f"<b>Murojaat matni:</b>\n{description}\n\n"
        f"<b>Maxfiylik turi:</b> {confidential}\n"
        f"<b>Biriktirilgan fayllar:</b> {files_text}\n\n"
        "<i>Ma'lumotlar to‘g‘riligini tasdiqlaysizmi? Tasdiqlaganingizdan so‘ng murojaat ro‘yxatga olinadi va mas'ullarga yetkaziladi.</i>"
    )
    return text


def format_appeal_detail_view(appeal: Appeal, is_staff: bool = False, viewer_role: str = "USER") -> str:
    """Detailed formatted text of an appeal for viewing."""
    applicant = appeal.applicant
    status_label = AppealStatus.label(appeal.status)
    confidential_label = "🔒 Maxfiy (Faqat Dekan)" if appeal.is_confidential else "🌐 Oddiy"

    files_count = len(appeal.files) if appeal.files else 0
    files_info = f"{files_count} ta fayl biriktirilgan" if files_count > 0 else "Fayl yo'q"

    text_parts = [
        f"📑 <b>MUROJAAT: {appeal.appeal_number}</b>\n",
        f"<b>Holati:</b> {status_label}",
        f"<b>Kelib tushgan sana:</b> {format_datetime(appeal.created_at)}",
        f"<b>Murojaat turi:</b> {appeal.appeal_type}",
        f"<b>Yo‘nalishi:</b> {appeal.topic_name}",
        f"<b>Mavzu:</b> {appeal.title}\n",
        f"<b>Mazmuni:</b>\n{appeal.description}\n",
        f"<b>Maxfiylik:</b> {confidential_label}",
        f"<b>Biriktirilgan fayllar:</b> {files_info}\n"
    ]

    # Staff / Admin details
    if is_staff:
        text_parts.append("<b>— Murojaatchi ma'lumotlari —</b>")
        if applicant:
            text_parts.append(f"<b>F.I.Sh:</b> {applicant.full_name}")
            text_parts.append(f"<b>Toifasi:</b> {UserType.label(applicant.user_type)}")
            text_parts.append(f"<b>Telefon:</b> {applicant.phone}")
            if applicant.user_type == UserType.TALABA.value:
                text_parts.append(f"<b>Yo‘nalish:</b> {applicant.direction or '-'} | <b>Kurs:</b> {applicant.course or '-'} | <b>Guruh:</b> {applicant.group_number or '-'}")
            elif applicant.user_type == UserType.FUQARO.value and applicant.region:
                text_parts.append(f"<b>Hudud:</b> {applicant.region}")
            elif applicant.user_type == UserType.OTA_ONA.value:
                text_parts.append(f"<b>Qarindoshlik:</b> {applicant.parent_relation or '-'} | <b>Farzand guruhi:</b> {applicant.child_group or '-'}")
            elif applicant.organization:
                text_parts.append(f"<b>Tashkilot:</b> {applicant.organization}")

        # Assignment details
        text_parts.append("\n<b>— Ijro nazorati —</b>")
        if appeal.assigned_to:
            text_parts.append(f"<b>Mas'ul xodim:</b> {appeal.assigned_to.full_name}")
            if appeal.assignment_note:
                text_parts.append(f"<b>Topshiriq izohi:</b> {appeal.assignment_note}")
            if appeal.deadline:
                text_parts.append(f"<b>Ijro muddati:</b> ⏳ {format_datetime(appeal.deadline)}")
        else:
            text_parts.append("<b>Mas'ul xodim:</b> Hali biriktirilmagan")

    # Rejection reason if rejected
    if appeal.status == AppealStatus.RAD_ETILDI.value and appeal.rejection_reason:
        text_parts.append(f"\n❌ <b>Rad etish sababi:</b>\n{appeal.rejection_reason}")

    # Official response if present
    if appeal.response_text:
        text_parts.append(f"\n🏛 <b>Rasmiy javob:</b>\n{appeal.response_text}")
        if appeal.responded_at:
            text_parts.append(f"<b>Javob berilgan sana:</b> {format_datetime(appeal.responded_at)}")

    return "\n".join(text_parts)
