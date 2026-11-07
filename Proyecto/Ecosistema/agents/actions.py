# Acciones posibles para un individuo.
from enum import Enum

class Action(Enum):
    # Acciones que un animal puede seleccionar durante un tick.
    MOVE = "MOVE"
    EAT = "EAT"
    HUNT = "HUNT"
    FLEE = "FLEE"
    REST = "REST"
    REPRODUCE = "REPRODUCE"