# All constants related to app service
from enum import Enum


class ModulesEnum(str, Enum):
    USER = 'USER'
    HEALTH = 'health'
    AUTH = 'auth'
    RESEARCH = 'research'
    PAPER = 'paper'
