from enum import StrEnum, auto


class DocTypes(StrEnum):
    RECEIPT = auto()
    CONSUME = auto()
    WRITEOFF = auto()
    RETURN = auto()
    CORRECTION = auto()