from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    choosing_user_type = State()
    
    # Common fields
    waiting_last_name = State()
    waiting_first_name = State()
    waiting_middle_name = State()
    waiting_full_name = State()
    waiting_phone = State()
    
    # Student specific
    waiting_direction = State()
    waiting_course = State()
    waiting_group = State()
    
    # Citizen specific
    waiting_region = State()
    
    # Parent specific
    waiting_relationship = State()
    waiting_child_group = State()
    
    # Employee / Other specific
    waiting_organization = State()
    
    # Consent
    waiting_consent = State()


class ProfileEditState(StatesGroup):
    choosing_field = State()
    waiting_value = State()

