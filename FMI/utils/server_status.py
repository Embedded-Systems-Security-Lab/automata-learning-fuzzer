import enum

class SUT_STATUS(enum.Enum):
    CRASH_BEFORE_SEND = 1
    CRASH_AFTER_SEND = 2
    DISCONNECTED = 3
    NO_CRASH = 4
