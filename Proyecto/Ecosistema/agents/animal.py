"""Individuos y estado basico de los animales."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from policies.rule_based import RuleBasedPolicy


class Species(Enum):
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"


@dataclass
class Animal:
    species: Species
    x: int
    y: int
    energy: float
    policy: RuleBasedPolicy
    identifier: str = ""
    alive: bool = True
    age: int = 0

    def __post_init__(self) -> None:
        if not self.identifier:
            self.identifier = str(uuid4())[:8]

    def act(self, world: "World") -> None:
        action = self.policy.choose_action(self, world)
        if action == "move":
            self._move(world)
        elif action == "eat":
            self._eat(world)
        elif action == "rest":
            self.energy += 0.1

        self.energy -= self._action_cost(action, world)
        self.age += 1
        if self.energy <= 0:
            self.alive = False

    def _move(self, world: "World") -> None:
        dx, dy = world.rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        new_x, new_y = self.x + dx, self.y + dy
        if world.in_bounds(new_x, new_y):
            self.x, self.y = new_x, new_y

    def _eat(self, world: "World") -> None:
        food = world.food_at(self.x, self.y)
        if food is not None:
            self.energy += food.energy
            world.foods.remove(food)

    def _action_cost(self, action: str, world: "World") -> float:
        if action == "move":
            return world.config.movement_cost + world.config.hunger_cost
        return world.config.hunger_cost
