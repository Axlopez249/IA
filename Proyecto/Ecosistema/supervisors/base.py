from __future__ import annotations
"""Contrato minimo para supervisores colectivos."""

from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING
from .objectives import Objective


if TYPE_CHECKING:
    from environment.world import World
    from agents.animal import Species

class Supervisor(Protocol):
    """Selecciona un objetivo para su especie en cada paso del mundo."""
    def choose_objective(self, world: "World") -> Objective:
        ...

@dataclass
class RuleBasedSupervisor:
    """Implementación basada en reglas para la Fase 3."""
    species: Species

    def choose_objective(self, world: "World") -> Objective:
        population = [a for a in world.animals if a.species == self.species and a.alive]
        pop_size = len(population)
        
        if pop_size == 0:
            return Objective.EXPLORE
            
        avg_energy = sum(a.energy for a in population) / pop_size

        is_herbivore = self.species.value == "herbivore"
        # 1. Alerta de Hambre: Si la energía promedio es crítica
        if avg_energy < world.config.initial_energy * 0.8:
            return Objective.SEARCH_FOOD if is_herbivore else Objective.HUNT
            
        # 2. Alerta de Extinción: Si quedan pocos individuos
        if pop_size < 10:
            return Objective.SURVIVE
            
        # 3. Oportunidad de Expansión: Buena energía y por debajo del límite
        limite = world.config.max_herbivores if is_herbivore else world.config.max_carnivores
        if avg_energy >= world.config.reproduction_energy_threshold and pop_size < limite:
            return Objective.GROUP
            
        # 4. Estado por defecto
        return Objective.EXPLORE