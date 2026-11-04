from aiogram.fsm.state import State, StatesGroup


class AppealSubmissionState(StatesGroup):
    choosing_type = State()           # Step 1: Ariza, Shikoyat, etc.
    choosing_topic = State()          # Step 2: Kafedra yo'nalishi
    entering_title = State()          # Step 3: Mavzu
    entering_description = State()    # Step 4: Mazmuni
    uploading_files = State()         # Step 5: Fayl biriktirish
    choosing_confidentiality = State()# Step 6: Maxfiylik (Oddiy / Maxfiy)
    confirming = State()              # Step 7: Yakuniy tasdiqlash

