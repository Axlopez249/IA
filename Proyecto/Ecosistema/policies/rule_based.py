# Politica determinista minima para la Fase 1.

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.actions import Action

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class RuleBasedPolicy:
    # Decide segun la especie y el estado inmediato del entorno.

    def choose_action(self, animal: "Animal", world: "World") -> "Action":
        # Selecciona una accion usando reglas sencillas y observaciones locales.
        partner = world.animal_at(animal.x, animal.y, animal.species, exclude=animal)
        if partner is not None and animal.can_reproduce(world.config):
            return Action.REPRODUCE

        if animal.species.value == "herbivore":
            if world.nearest_predator(animal) is not None:
                return Action.FLEE
            if world.food_at(animal.x, animal.y) is not None:
                return Action.EAT
            if animal.energy >= world.config.rest_energy_threshold:
                return Action.REST
            return Action.MOVE

        if world.animal_at(animal.x, animal.y, "herbivore") is not None:
            return Action.HUNT
        if animal.energy >= world.config.rest_energy_threshold:
            return Action.REST
        return Action.MOVE
