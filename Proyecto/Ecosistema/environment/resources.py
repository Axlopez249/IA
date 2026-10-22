"""Recursos simples disponibles en el mapa."""

from dataclasses import dataclass


@dataclass
class Food:
    x: int
    y: int
    energy: float = 4.0


@dataclass
class Water:
    x: int
    y: int
