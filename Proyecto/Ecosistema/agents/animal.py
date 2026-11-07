# Individuos y estado basico de los animales.
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from .actions import Action
from policies.base import Policy
from supervisors.objectives import Objective

if TYPE_CHECKING:
    from config import SimulationConfig
    from environment.world import World

class Species(Enum):
    # Especies disponibles en el ecosistema.
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"

class Variation(Enum):
    # Carnívoras
    C_RESISTANT = "c_resistant" # Lenta pero aguanta mucho (1 acción, metabolismo bajo)
    C_FAST = "c_fast"           # Rápida pero gasta más (2 acciones, metabolismo alto)
    # Herbívoras
    H_NORMAL = "h_normal"       # Balanceada (2 acciones, metabolismo normal)
    H_FAST = "h_fast"           # Muy rápida pero aguanta poco (3 acciones, metabolismo alto)
    H_SLOW = "h_slow"           # Muy lenta pero muy resistente (1 acción, metabolismo bajo)

@dataclass
class Animal:
    # Representa un individuo con posicion, energia, edad y politica.
    species: Species
    x: int
    y: int
    energy: float
    policy: Policy
    variation: Variation | None = None
    identifier: str = ""
    alive: bool = True
    age: int = 0
    objective: Objective | None = None

    def __post_init__(self) -> None:
        # Asigna un identificador corto cuando el individuo no tiene uno.
        if not self.identifier:
            self.identifier = str(uuid4())[:8]
        if self.variation is None:
            self.variation = Variation.H_NORMAL if self.species == Species.HERBIVORE else Variation.C_FAST

    # Retorna la cantidad de acciones por turno y el multiplicador de metabolismo segun la variacion.
    def get_traits(self) -> tuple[int, float]:
            if self.variation == Variation.H_NORMAL:
                return 2, 1.0
            elif self.variation == Variation.H_FAST:
                return 3, 1.5
            elif self.variation == Variation.H_SLOW:
                return 1, 0.5
            elif self.variation == Variation.C_RESISTANT:
                return 1, 0.5
            elif self.variation == Variation.C_FAST:
                return 2, 1.2
            return 1, 1.0
    
    def can_reproduce(self, config: "SimulationConfig") -> bool:
        # Indica si el individuo cumple las condiciones basicas para reproducirse.
        return self.age >= config.reproduction_age and self.energy >= config.reproduction_energy_threshold

    def act(self, world: "World") -> None:
            if not self.alive:
                return
            
            speed, _ = self.get_traits()
            
            # El ave ejecuta 'X' cantidad de acciones dependiendo de su velocidad
            for _ in range(speed):
                if not self.alive:
                    break
                action = self.policy.choose_action(self, world)
                self.execute_action(action, world)

    def execute_action(self, action: Action, world: "World") -> None:
        # Ejecuta una accion concreta; tambien sirve para futuros entornos de entrenamiento.
        if action == Action.MOVE:
            self.move(world)
        elif action == Action.EAT:
            self.eat(world)
        elif action == Action.HUNT:
            self.hunt(world)
        elif action == Action.FLEE:
            self.flee(world)
        elif action == Action.REST:
            self.energy += world.config.rest_recovery_rate
        elif action == Action.REPRODUCE:
            world.queue_reproduction(self)

        self.energy -= self.calculate_action_cost(action, world)
        self.energy = min(self.energy, world.config.max_energy)
        
        # Envejecen con cada acción, haciendo que las aves rápidas vivan menos turnos
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
            self.energy += world.config.food_energy
            if food in world.foods:
                world.foods.remove(food)

    def hunt(self, world: "World") -> None:
            if self.species != Species.CARNIVORE:
                return
            prey = world.animal_at(self.x, self.y, Species.HERBIVORE)
            if prey is not None and prey.alive:
                prey.alive = False
                self.energy += world.config.hunt_energy_gain
                world.hunts += 1

    def calculate_action_cost(self, action: Action, world: "World") -> float:
            _, metabolism = self.get_traits()
            base_cost = world.config.hunger_cost
            
            if action in (Action.MOVE, Action.FLEE):
                base_cost += world.config.movement_cost
            elif action == Action.REPRODUCE:
                base_cost += world.config.reproduction_cost
                
            return base_cost * metabolism