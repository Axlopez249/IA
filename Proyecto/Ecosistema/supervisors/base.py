"""Contrato minimo para supervisores colectivos."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from .objectives import Objective

if TYPE_CHECKING:
    from environment.world import World


class Supervisor(Protocol):
    """Selecciona un objetivo para su especie en cada paso del mundo."""

    def choose_objective(self, world: "World") -> Objective:
        ...
