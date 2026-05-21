from enum import Enum, auto
from typing import Any, Optional


class ArtifactType(Enum):
    TRANSCRIPT = auto()
    SUMMARY = auto()
    
    @classmethod
    def _missing_(cls, value: object) -> Optional["ArtifactType"]:
        assert type(value) == str
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


# TRANSCRIPT_PRIORITY: tuple[str,...] = (
#     'dense',
#     'text',
#     'json',
#     'raw',
#     'other',
# )


class TranscriptPriority(Enum):
    DENSE = auto()
    TEXT = auto()
    JSON = auto()
    RAW = auto()
    OTHER = auto()

    @classmethod
    def ordered(cls) -> tuple["TranscriptPriority",...]:
        return tuple(cls)
    
    @classmethod
    def _missing_(cls, value: object) -> Optional["TranscriptPriority"]:
        assert type(value) == str
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None
