# Recursos simples disponibles en el mapa.

from dataclasses import dataclass


@dataclass
class Food:
    # Recurso que un herbivoro puede consumir para recuperar energia.

    x: int
    y: int
    energy: float = 4.0


@dataclass
class Water:
    # Punto de agua reservado para una futura extension del entorno.

    x: int
    y: int
