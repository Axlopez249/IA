"""Política de referencia que elige uniformemente una acción válida."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from agents.actions import Action
from agents.animal import Species
from policies.base import Policy

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class RandomPolicy(Policy):
    """Baseline mínimo para comprobar si el agente aprendió algo."""

    # Inicializa la política aleatoria con la especie y una semilla para reproducibilidad
    def __init__(self, species: Species, seed: int = 0) -> None:
        self.species = species
        self.random = random.Random(seed)

    # Devuelve las acciones válidas para la especie correspondiente
    def valid_actions(self) -> tuple[Action, ...]:
        if self.species == Species.HERBIVORE:
            return (
                Action.MOVE,
                Action.EAT,
                Action.FLEE,
                Action.REST,
                Action.REPRODUCE,
            )
        return (
            Action.MOVE,
            Action.HUNT,
            Action.FLEE,
            Action.REST,
            Action.REPRODUCE,
        )
    # Elige una acción aleatoria de las acciones válidas para el animal dado y el mundo
    def choose_action(self, animal: "Animal", world: "World") -> Action:
        return self.random.choice(self.valid_actions())
