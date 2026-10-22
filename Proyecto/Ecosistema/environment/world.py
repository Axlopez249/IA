"""Mapa 2D y ciclo temporal de la simulacion."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from config import SimulationConfig
from .resources import Food


@dataclass
class World:
    config: SimulationConfig
    rng: random.Random = field(init=False)
    foods: list[Food] = field(default_factory=list)
    animals: list["Animal"] = field(default_factory=list)
    step_count: int = 0

    def __post_init__(self) -> None:
        self.rng = random.Random(self.config.seed)

    def add_animal(self, animal: "Animal") -> None:
        self.animals.append(animal)

    def add_food(self, food: Food) -> None:
        if self.in_bounds(food.x, food.y):
            self.foods.append(food)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.config.width and 0 <= y < self.config.height

    def random_position(self) -> tuple[int, int]:
        return (
            self.rng.randrange(self.config.width),
            self.rng.randrange(self.config.height),
        )

    def food_at(self, x: int, y: int) -> Food | None:
        return next((food for food in self.foods if food.x == x and food.y == y), None)

    def step(self) -> None:
        """Ejecuta un tick: accion, consumo, coste energetico y limpieza."""
        for animal in list(self.animals):
            if animal.alive:
                animal.act(self)
        self._regrow_food()
        self.animals = [animal for animal in self.animals if animal.alive]
        self.step_count += 1

    def _regrow_food(self) -> None:
        attempts = int(self.config.width * self.config.height * self.config.food_regrowth_rate)
        for _ in range(attempts):
            if self.rng.random() < self.config.food_regrowth_rate:
                x, y = self.random_position()
                if self.food_at(x, y) is None:
                    self.add_food(Food(x, y, self.config.food_energy))
