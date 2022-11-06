#!/usr/bin/env python3
from enum import IntEnum, auto


class timeAT(IntEnum):
    TIME = 0
    YEAR = auto()
    MONTH = auto()
    DAY = auto()
    HOUR = auto()
    MINUTE = auto()
    SECONDS = auto()
    ZONE = auto()
    TIME_MAX = auto()
class messageNotiAT(IntEnum):
    NUMBER = 0
    TIME = auto()
    YEAR = auto()
    MONTH = auto()
    DAY = auto()
    HOUR = auto()
    MINUTE = auto()
    SECONDS = auto()
    ZONE = auto()
    TIME_MAX = auto()