# Mapa 2D y ciclo temporal de la simulacion.

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from agents.actions import Action
from agents.animal import Species
from .resources import Food

if TYPE_CHECKING:
    from supervisors.base import Supervisor
    from supervisors.objectives import Objective
    from config import SimulationConfig
    from agents.animal import Animal


@dataclass
class World:
    config: "SimulationConfig"
    rng: random.Random = field(init=False)
    foods: list[Food] = field(default_factory=list)
    animals: list["Animal"] = field(default_factory=list)
    reproduction_requests: list["Animal"] = field(default_factory=list)
    step_count: int = 0
    births: int = 0
    deaths: int = 0
    hunts: int = 0
    supervisors: dict[Species, "Supervisor"] = field(default_factory=dict)
    objectives: dict[Species, "Objective | None"] = field(default_factory=dict)
    last_actions: dict[str, Action] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Crea el generador aleatorio usando la semilla de la configuracion.
        self.rng = random.Random(self.config.seed)

    def add_animal(self, animal: "Animal") -> None:
        # Añade un animal a la poblacion del mundo.
        self.animals.append(animal)

    def add_food(self, food: Food) -> None:
        # Añade comida solo cuando sus coordenadas estan dentro del mapa.
        if self.in_bounds(food.x, food.y):
            self.foods.append(food)

    def in_bounds(self, x: int, y: int) -> bool:
        # Comprueba si una coordenada pertenece al mapa.
        return 0 <= x < self.config.width and 0 <= y < self.config.height

    def random_position(self) -> tuple[int, int]:
        # Genera una posicion aleatoria valida dentro del mapa.
        return (
            self.rng.randrange(self.config.width),
            self.rng.randrange(self.config.height),
        )

    def food_at(self, x: int, y: int) -> Food | None:
        # Devuelve la primera comida situada en una coordenada exacta.
        return next((food for food in self.foods if food.x == x and food.y == y), None)

    def animal_at(
        self,
        x: int,
        y: int,
        species: object,
        exclude: "Animal | None" = None,
    ) -> "Animal | None":
        # Busca un animal vivo de una especie en una coordenada concreta.
        species_value = species.value if hasattr(species, "value") else species
        return next(
            (
                animal
                for animal in self.animals
                if animal.alive
                and animal is not exclude
                and animal.x == x
                and animal.y == y
                and animal.species.value == species_value
            ),
            None,
        )

    def distance(self, first: "Animal", second: "Animal | Food") -> int:
        # Calcula la distancia Manhattan entre un animal y otro objeto del mapa.
        return abs(first.x - second.x) + abs(first.y - second.y)

    def nearest_food(self, animal: "Animal") -> Food | None:
        # Devuelve la comida visible mas cercana dentro del radio de percepcion.
        visible_food = (
            food for food in self.foods
            if self.distance(animal, food) <= self.config.perception_radius
        )
        return min(visible_food, key=lambda food: self.distance(animal, food), default=None)

    def nearest_prey(self, animal: "Animal") -> "Animal | None":
        # Devuelve la presa herbivora visible mas cercana.
        prey = (candidate for candidate in self.animals
            if candidate.alive
            and candidate.species.value == "herbivore"
            and self.distance(animal, candidate) <= self.config.perception_radius)
        return min(prey, key=lambda candidate: self.distance(animal, candidate), default=None)

    def nearest_predator(self, animal: "Animal") -> "Animal | None":
        # Devuelve el depredador visible mas cercano o None si no hay uno.
        visible_predators = []
        for candidate in self.animals:
            if not candidate.alive:
                continue
            if candidate.species.value != "carnivore":
                continue
            if self.distance(animal, candidate) > self.config.perception_radius:
                continue
            visible_predators.append(candidate)

        if not visible_predators:
            return None

        return min(
            visible_predators,
            key=lambda candidate: self.distance(animal, candidate),
        )

    def nearest_reproduction_partner(self, animal: "Animal") -> "Animal | None":
        """Devuelve la pareja elegible más cercana para el objetivo GROUP."""
        candidates = (
            candidate
            for candidate in self.animals
            if candidate.alive
            and candidate is not animal
            and candidate.species == animal.species
            and candidate.can_reproduce(self.config)
        )
        return min(
            candidates,
            key=lambda candidate: self.distance(animal, candidate),
            default=None,
        )

    def queue_reproduction(self, animal: "Animal") -> None:
        # Registra una solicitud de reproduccion sin duplicarla.
        if (
            animal.alive
            and animal.can_reproduce(self.config)
            and animal not in self.reproduction_requests
        ):
            self.reproduction_requests.append(animal)

    def step(self) -> None:
        # Ejecuta un tick, resuelve reproduccion, muertes y regeneracion.
        self.last_actions.clear()
        self.update_objectives()
        for animal in list(self.animals):
            if animal.alive:
                animal.objective = self.objectives.get(animal.species)
                animal.act(self)
        self.resolve_reproduction()
        self.deaths += sum(not animal.alive for animal in self.animals)
        self.regrow_food()
        self.animals = [animal for animal in self.animals if animal.alive]
        self.step_count += 1

    def update_objectives(self) -> None:
        """Actualiza una vez por especie los objetivos de supervisores activos."""
        self.objectives = {
            species: supervisor.choose_objective(self)
            for species, supervisor in self.supervisors.items()
        }

    def resolve_reproduction(self) -> None:
            from agents.animal import Animal
            used: set[str] = set()
            
            for first in self.reproduction_requests:
                if (
                    first.identifier in used
                    or not first.alive
                ):
                    continue
                partner = next(
                    (
                        candidate
                        for candidate in self.reproduction_requests
                        if candidate.identifier not in used
                        and candidate is not first
                        and candidate.alive
                        and candidate.species == first.species
                        and candidate.x == first.x
                        and candidate.y == first.y
                    ),
                    None,
                )
                
                if partner is None:
                    continue

                population_limit = (
                    self.config.max_herbivores
                    if first.species.value == "herbivore"
                    else self.config.max_carnivores
                )
                current_population = sum(
                    animal.alive and animal.species == first.species
                    for animal in self.animals
                )
                if current_population >= population_limit:
                    continue

                first.energy -= self.config.reproduction_cost
                partner.energy -= self.config.reproduction_cost
                
                # El hijo hereda la variación de su progenitor
                child = Animal(
                    species=first.species, 
                    x=first.x, 
                    y=first.y, 
                    energy=self.config.initial_energy, 
                    policy=first.policy,
                    variation=first.variation  
                )
                self.animals.append(child)
                self.births += 1
                used.update((first.identifier, partner.identifier))
                
            self.reproduction_requests.clear()

    def regrow_food(self) -> None:
        attempts = int(self.config.width * self.config.height * self.config.food_regrowth_rate)
        for _ in range(attempts):
            if self.rng.random() < self.config.food_regrowth_rate:
                x, y = self.random_position()
                if self.food_at(x, y) is None:
                    self.add_food(Food(x, y, self.config.food_energy))