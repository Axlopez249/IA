"""Política basada en reglas que obedece al supervisor."""

from __future__ import annotations
from typing import TYPE_CHECKING
from agents.actions import Action
from policies.base import Policy
from supervisors.base import action_for_objective

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class RuleBasedPolicy(Policy):
    def choose_action(self, animal: "Animal", world: "World") -> Action:
        # Las órdenes colectivas tienen prioridad sobre la política individual.
        supervised_action = action_for_objective(animal, world)
        if supervised_action is not None:
            return supervised_action

        # CAPA 1: INSTINTO DE SUPERVIVENCIA INMEDIATA
        from agents.animal import Species
        if animal.species == Species.HERBIVORE:
            predator = world.nearest_predator(animal)
            # Si el depredador está muy cerca (radio <= 2), huir es prioridad absoluta
            if predator and world.distance(animal, predator) <= 2:
                return Action.FLEE
                
            # Si hay comida en la misma celda, comerla
            if world.food_at(animal.x, animal.y):
                return Action.EAT
        
        elif animal.species == Species.CARNIVORE:
            # Si hay una presa viva en su misma celda, cazarla
            if world.animal_at(animal.x, animal.y, Species.HERBIVORE):
                return Action.HUNT

        # Toman descansos preventivos si la energía baja del umbral
        if animal.energy < world.config.rest_energy_threshold:
            return Action.REST
            
        return Action.MOVE