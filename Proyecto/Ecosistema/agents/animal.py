# Individuos y estado basico de los animales.

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from .actions import Action
from policies.rule_based import RuleBasedPolicy

if TYPE_CHECKING:
    from config import SimulationConfig
    from environment.world import World


class Species(Enum):
    # Especies disponibles en el ecosistema.

    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"


@dataclass
class Animal:
    # Representa un individuo con posicion, energia, edad y politica.

    species: Species
    x: int
    y: int
    energy: float
    policy: RuleBasedPolicy
    identifier: str = ""
    alive: bool = True
    age: int = 0

    def __post_init__(self) -> None:
        # Asigna un identificador corto cuando el individuo no tiene uno.
        if not self.identifier:
            self.identifier = str(uuid4())[:8]

    def can_reproduce(self, config: "SimulationConfig") -> bool:
        # Indica si el individuo cumple las condiciones basicas para reproducirse.
        return self.age >= config.reproduction_age and self.energy >= config.reproduction_energy_threshold

    def act(self, world: "World") -> None:
        # Selecciona y ejecuta una accion, actualiza edad y comprueba su muerte.
        action = self.policy.choose_action(self, world)
        if action == Action.MOVE:
            self.move(world)
        elif action == Action.EAT:
            self.eat(world)
        elif action == Action.HUNT:
            self.hunt(world)
        elif action == Action.FLEE:
            self.flee(world)
        elif action == Action.REST:
            self.energy += 0.1
        elif action == Action.REPRODUCE:
            world.queue_reproduction(self)

        self.energy -= self.calculate_action_cost(action, world)
        self.age += 1
        if self.energy <= 0 or self.age >= world.config.max_age:
            self.alive = False

    def move(self, world: "World") -> None:
        # Avanza hacia un objetivo visible o explora en una direccion aleatoria.
        target = world.nearest_food(self) if self.species == Species.HERBIVORE else world.nearest_prey(self)
        if target is None:
            dx, dy = world.rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        else:
            dx = (target.x > self.x) - (target.x < self.x)
            dy = (target.y > self.y) - (target.y < self.y)
            if dx and dy:
                dy = 0
        new_x, new_y = self.x + dx, self.y + dy
        if world.in_bounds(new_x, new_y):
            self.x, self.y = new_x, new_y

    def flee(self, world: "World") -> None:
        # Se aleja del depredador visible mas cercano.
        predator = world.nearest_predator(self)
        if predator is None:
            self.move(world)
            return
        dx = (self.x > predator.x) - (self.x < predator.x)
        dy = (self.y > predator.y) - (self.y < predator.y)
        if abs(predator.x - self.x) >= abs(predator.y - self.y):
            dy = 0
        else:
            dx = 0
        new_x, new_y = self.x + dx, self.y + dy
        if world.in_bounds(new_x, new_y):
            self.x, self.y = new_x, new_y

    def eat(self, world: "World") -> None:
        # Consume la comida de su casilla si el individuo es herbivoro.
        if self.species != Species.HERBIVORE:
            return
        food = world.food_at(self.x, self.y)
        if food is not None:
            self.energy += food.energy
            world.foods.remove(food)

    def hunt(self, world: "World") -> None:
        # Caza un herbivoro que comparta su casilla y obtiene energia.
        if self.species != Species.CARNIVORE:
            return
        prey = world.animal_at(self.x, self.y, Species.HERBIVORE)
        if prey is not None:
            prey.alive = False
            self.energy += world.config.hunt_energy
            world.hunts += 1

    def calculate_action_cost(self, action: Action, world: "World") -> float:
        # Calcula el coste energetico de una accion individual.
        if action in (Action.MOVE, Action.FLEE):
            return world.config.movement_cost + world.config.hunger_cost
        if action == Action.REPRODUCE:
            return world.config.reproduction_cost + world.config.hunger_cost
        return world.config.hunger_cost
