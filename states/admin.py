from aiogram.fsm.state import State, StatesGroup


class AdminSearchState(StatesGroup):
    waiting_query = State()


class AdminAssignState(StatesGroup):
    waiting_staff_select = State()
    waiting_instruction = State()
    waiting_deadline = State()


class AdminResponseState(StatesGroup):
    waiting_response_text = State()


class AdminRejectState(StatesGroup):
    waiting_rejection_reason = State()


class AdminInternalNoteState(StatesGroup):
    waiting_note = State()


class AdminStaffManageState(StatesGroup):
    waiting_tg_id = State()
    waiting_full_name = State()
    waiting_phone = State()
    waiting_role = State()
    waiting_position = State()


class AdminBroadcastState(StatesGroup):
    waiting_message = State()
    confirm_send = State()


class AdminSettingsState(StatesGroup):
    waiting_value = State()
    waiting_topic_name = State()


class CorrespondenceState(StatesGroup):
    waiting_message = State()
