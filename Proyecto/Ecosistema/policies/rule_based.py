"""Política basada en reglas que obedece al supervisor."""

from __future__ import annotations
from typing import TYPE_CHECKING
from agents.actions import Action
from policies.base import Policy
from supervisors.objectives import Objective

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class RuleBasedPolicy(Policy):
    def choose_action(self, animal: "Animal", world: "World") -> Action:
        # Selecciona una acción basada en reglas y el objetivo del supervisor.

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

        # CAPA 2: INTELIGENCIA DE ENJAMBRE (SUPERVISOR)
        objective = animal.objective

        # Objetivo: MULTIPLICARSE / AGRUPARSE
        if objective == Objective.GROUP:
            if animal.can_reproduce(world.config):
                # Verificar si hay una pareja compatible en la misma celda
                mate = world.animal_at(animal.x, animal.y, animal.species, exclude=animal)
                if mate and mate.can_reproduce(world.config):
                    return Action.REPRODUCE
            # Si no hay pareja en la celda, moverse por el mapa para encontrar una
            return Action.MOVE

        # Objetivo: ALIMENTARSE / CAZAR
        if objective in (Objective.SEARCH_FOOD, Objective.HUNT):
            # La acción instintiva de comer/cazar ya se evaluó en la Capa 1. 
            # Si llegamos aquí es porque no hay alimento en esta celda,
            # así que la acción lógica obligatoria es moverse para buscarlo.
            return Action.MOVE

        # Objetivo: SOBREVIVIR (Población en riesgo de extinción)
        if objective == Objective.SURVIVE:
            # Conservar energía es la máxima prioridad
            if animal.energy < world.config.max_energy * 0.8:
                return Action.REST
            return Action.MOVE

        # Objetivo: EXPLORAR (Estado de bienestar por defecto)
        # Toman descansos preventivos si la energía baja del umbral
        if animal.energy < world.config.rest_energy_threshold:
            return Action.REST
            
        return Action.MOVE