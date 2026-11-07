"""Objetivos colectivos que un supervisor puede comunicar a una especie."""

from enum import Enum


class Objective(Enum):
    EXPLORE = "explore"
    SEARCH_FOOD = "search_food"
    HUNT = "hunt"
    FLEE = "flee"
    GROUP = "group"
    SURVIVE = "survive"
