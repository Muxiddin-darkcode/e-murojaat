from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User, Appeal, AppealStatus, UserRole


def get_admin_main_menu(is_super_admin: bool = False, is_dekan: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📥 Yangi murojaatlar", callback_data="admin_nav:list:YANGI", style="success"),
            InlineKeyboardButton(text="📂 Barcha murojaatlar", callback_data="admin_nav:list:ALL", style="primary")
        ],
        [
            InlineKeyboardButton(text="🔄 Ko‘rib chiqilayotganlar", callback_data="admin_nav:list:KORIB_CHIQILMOQDA", style="primary"),
            InlineKeyboardButton(text="⏳ Javob kutilayotganlar", callback_data="admin_nav:list:PENDING_RESPONSE", style="primary")
        ],
        [
            InlineKeyboardButton(text="✅ Hal qilinganlar", callback_data="admin_nav:list:HAL_QILINDI", style="success"),
            InlineKeyboardButton(text="❌ Rad etilganlar", callback_data="admin_nav:list:RAD_ETILDI", style="danger")
        ],
        [
            InlineKeyboardButton(text="🔎 Murojaatni qidirish", callback_data="admin_nav:search", style="primary"),
            InlineKeyboardButton(text="📊 Statistika va hisobotlar", callback_data="admin_nav:statistics", style="primary")
        ]
    ]

    # Staff management
    if is_super_admin or is_dekan:
        buttons.append([
            InlineKeyboardButton(text="👥 Xodimlarni boshqarish", callback_data="admin_nav:staff", style="primary"),
            InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_nav:broadcast", style="primary")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_nav:broadcast", style="primary")
        ])

    # Settings
    if is_super_admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Bot sozlamalari", callback_data="admin_nav:settings", style="primary")])

    buttons.append([InlineKeyboardButton(text="⬅️ Foydalanuvchi menyusi", callback_data="admin_nav:exit", style="danger")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_appeal_card_actions(
    appeal: Appeal,
    current_user_role: str,
    back_filter: str = "ALL",
    back_page: int = 1
) -> InlineKeyboardMarkup:
    buttons = []

    # If appeal is new, allow "Ko'rib chiqishga olish"
    if appeal.status in [AppealStatus.YANGI.value, AppealStatus.ROYXATGA_OLINDI.value]:
        buttons.append([
            InlineKeyboardButton(text="🔄 Ko‘rib chiqishga olish", callback_data=f"adm_act:take:{appeal.id}", style="success")
        ])

    # Assignment button (Dekan and Admins)
    if current_user_role in [UserRole.SUPER_ADMIN.value, UserRole.DEKAN.value, UserRole.ADMINISTRATOR.value]:
        assign_label = "👤 Mas'ulni o‘zgartirish" if appeal.assigned_to_id else "👤 Mas'ulga biriktirish"
        buttons.append([
            InlineKeyboardButton(text=assign_label, callback_data=f"adm_act:assign:{appeal.id}", style="primary")
        ])

    # Response & Note
    buttons.append([
        InlineKeyboardButton(text="📨 Javob yuborish", callback_data=f"adm_act:respond:{appeal.id}", style="success"),
        InlineKeyboardButton(text="📝 Izoh qoldirish", callback_data=f"adm_act:note:{appeal.id}", style="primary")
    ])

    # Resolution & Rejection
    if appeal.status not in [AppealStatus.HAL_QILINDI.value, AppealStatus.RAD_ETILDI.value]:
        buttons.append([
            InlineKeyboardButton(text="✅ Hal qilindi", callback_data=f"adm_act:resolve:{appeal.id}", style="success"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_act:reject:{appeal.id}", style="danger")
        ])

    # Correspondence
    buttons.append([
        InlineKeyboardButton(text="💬 Murojaatchi bilan yozishmalar", callback_data=f"adm_act:chat:{appeal.id}", style="primary")
    ])

    # Back button
    buttons.append([
        InlineKeyboardButton(text="⬅️ Ro‘yxatga qaytish", callback_data=f"admin_nav:list:{back_filter}:{back_page}", style="primary"),
        InlineKeyboardButton(text="🏠 Admin menyu", callback_data="admin_nav:menu", style="danger")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_appeals_pagination(
    appeals: List[Appeal],
    current_page: int,
    total_count: int,
    limit: int,
    status_filter: str
) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_count + limit - 1) // limit)
    buttons = []

    # Appeal rows
    for app in appeals:
        status_emoji = AppealStatus.label(app.status)[:2]
        title_snippet = (app.title[:20] + "...") if len(app.title) > 20 else app.title
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {app.appeal_number} | {title_snippet}",
                callback_data=f"adm_view:{app.id}:{status_filter}:{current_page}"
            )
        ])

    # Pagination navigation
    nav_row = []
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_nav:list:{status_filter}:{current_page - 1}")
        )
    
    nav_row.append(
        InlineKeyboardButton(text=f"📄 {current_page}/{total_pages} ({total_count})", callback_data="noop")
    )

    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_nav:list:{status_filter}:{current_page + 1}")
        )
    
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(text="🏠 Admin Bosh Menyu", callback_data="admin_nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_staff_selection_keyboard(staff_list: List[User], appeal_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for staff in staff_list:
        role_title = UserRole.label(staff.role)
        pos = f" ({staff.staff_position})" if staff.staff_position else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {staff.full_name}{pos} - {role_title}",
                callback_data=f"staff_sel:{appeal_id}:{staff.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"adm_view:{appeal_id}:ALL:1")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_deadline_keyboard(appeal_id: int, staff_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⚡️ 1 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:1"),
            InlineKeyboardButton(text="📅 3 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:3")
        ],
        [
            InlineKeyboardButton(text="📆 5 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:5"),
            InlineKeyboardButton(text="🗓 10 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:10")
        ],
        [
            InlineKeyboardButton(text="🕒 15 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:15"),
            InlineKeyboardButton(text="⏳ 30 kun", callback_data=f"set_dl:{appeal_id}:{staff_id}:30")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"adm_view:{appeal_id}:ALL:1")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_statistics_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📅 Bugungi statistika", callback_data="stats_period:today"),
            InlineKeyboardButton(text="🗓 Haftalik statistika", callback_data="stats_period:week")
        ],
        [
            InlineKeyboardButton(text="📊 Oylik statistika", callback_data="stats_period:month"),
            InlineKeyboardButton(text="📈 Barcha davr", callback_data="stats_period:all")
        ],
        [
            InlineKeyboardButton(text="📥 Excel hisobot (.xlsx) yuklab olish", callback_data="stats_export:excel")
        ],
        [InlineKeyboardButton(text="🏠 Admin menyu", callback_data="admin_nav:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🏛 Institut nomi", callback_data="set_edit:institute_name")],
        [InlineKeyboardButton(text="📚 Fakultet nomi", callback_data="set_edit:department_name")],
        [InlineKeyboardButton(text="👤 Dekan F.I.Sh.", callback_data="set_edit:dekan_name")],
        [InlineKeyboardButton(text="📞 Aloqa telefoni", callback_data="set_edit:contact_phone")],
        [InlineKeyboardButton(text="✈️ Rasmiy Telegram", callback_data="set_edit:official_telegram")],
        [InlineKeyboardButton(text="⏱ Standart ijro muddati (kun)", callback_data="set_edit:default_deadline_days")],
        [InlineKeyboardButton(text="🗂 Murojaat yo‘nalishlarini boshqarish", callback_data="set_edit:topics")],
        [InlineKeyboardButton(text="🏠 Admin menyu", callback_data="admin_nav:menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

