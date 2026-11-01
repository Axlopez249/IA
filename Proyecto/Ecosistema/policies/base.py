# Contrato comun para las politicas de los animales.

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from agents.actions import Action

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class Policy(Protocol):
    # Cualquier politica debe convertir una observacion en una accion valida.

    def choose_action(self, animal: "Animal", world: "World") -> Action:
        # Selecciona la accion que ejecutara el animal durante este tick.
        ...