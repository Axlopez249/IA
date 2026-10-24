# Acciones posibles para un individuo.

from enum import Enum


class Action(Enum):
    # Acciones que un animal puede seleccionar durante un tick.

    MOVE = "move"
    EAT = "eat"
    HUNT = "hunt"
    FLEE = "flee"
    REST = "rest"
    REPRODUCE = "reproduce"