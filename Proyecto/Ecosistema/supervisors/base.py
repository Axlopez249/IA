from __future__ import annotations
"""Contrato minimo para supervisores colectivos."""

from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING
from agents.actions import Action
from .objectives import Objective


if TYPE_CHECKING:
    from environment.world import World
    from agents.animal import Animal, Species

class Supervisor(Protocol):
    """Selecciona un objetivo para su especie en cada paso del mundo."""
    def choose_objective(self, world: "World") -> Objective | None:
        ...

@dataclass
class RuleBasedSupervisor:
    """Implementación basada en reglas para la Fase 3."""
    species: Species

    def choose_objective(self, world: "World") -> Objective | None:
        population = [a for a in world.animals if a.species == self.species and a.alive]
        pop_size = len(population)
        
        if pop_size == 0:
            return None
            
        avg_energy = sum(a.energy for a in population) / pop_size

        is_herbivore = self.species.value == "herbivore"
        minimum_population = (
            world.config.min_herbivores
            if is_herbivore
            else world.config.min_carnivores
        )

        # 1. Recuperación poblacional: si hay energía suficiente, agrupar
        # individuos tiene prioridad para intentar recuperar la especie.
        if pop_size < minimum_population:
            if avg_energy >= world.config.reproduction_energy_threshold:
                return Objective.GROUP

            # Sin energía suficiente no es posible reproducirse; conservar la
            # respuesta de supervivencia evita que la población se desplace
            # sin alimentarse mientras intenta agruparse.
            return Objective.SURVIVE

        # 2. Alerta de Hambre: Si la energía promedio es crítica.
        if avg_energy < world.config.initial_energy * 0.8:
            return Objective.SEARCH_FOOD if is_herbivore else Objective.HUNT
            
        # 3. Oportunidad de Expansión: Buena energía y por debajo del límite.
        limite = world.config.max_herbivores if is_herbivore else world.config.max_carnivores
        if avg_energy >= world.config.reproduction_energy_threshold and pop_size < limite:
            return Objective.GROUP
            
        # 4. Estado por defecto
        return None


def action_for_objective(
    animal: "Animal",
    world: "World",
) -> Action | None:
    """Convierte una orden colectiva activa en una acción individual."""
    objective = animal.objective
    if objective is None or objective == Objective.EXPLORE:
        return None

    if objective == Objective.FLEE:
        return Action.FLEE

    if objective == Objective.SEARCH_FOOD:
        return Action.EAT if world.food_at(animal.x, animal.y) else Action.MOVE

    if objective == Objective.HUNT:
        from agents.animal import Species

        if world.animal_at(animal.x, animal.y, Species.HERBIVORE) is not None:
            return Action.HUNT
        return Action.MOVE

    if objective == Objective.GROUP:
        if animal.can_reproduce(world.config):
            mate = world.animal_at(
                animal.x,
                animal.y,
                animal.species,
                exclude=animal,
            )
            if mate and mate.can_reproduce(world.config):
                return Action.REPRODUCE
        return Action.MOVE

    if objective == Objective.SURVIVE:
        return Action.REST

    return None