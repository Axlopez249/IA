# Configuracion central de la simulacion.

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    width: int = 30
    height: int = 20
    initial_herbivores: int = 50
    initial_carnivores: int = 20
    initial_food: int = 45
    food_regrowth_rate: float = 0.08
    
    # Costos y ganancias de energía
    initial_energy: float = 30.0
    max_energy: float = 60.0
    movement_cost: float = 1.0
    hunger_cost: float = 0.2
    food_energy: float = 10.0      # Ganancia por comer planta
    hunt_energy_gain: float = 20.0 # Ganancia por cazar
    rest_recovery_rate: float = 2.5
    rest_energy_threshold: float = 18.0
    hunt_energy: float = 7.0
    
    # Reglas de reproducción
    reproduction_age: int = 5
    reproduction_energy_threshold: float = 40.0
    reproduction_cost: float = 15.0
    
    # Otros límites
    max_steps: int = 100
    seed: int = 7
    max_age: int = 300
    perception_radius: int = 5
    max_herbivores: int = 100
    max_carnivores: int = 50
	
    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("El ancho y el alto deben ser mayores que cero.")
        if any(value < 0 for value in (
            self.initial_herbivores,
            self.initial_carnivores,
            self.initial_food,
            self.max_steps,
            self.max_age,
            self.perception_radius,
        )):
            raise ValueError("Las cantidades y limites no pueden ser negativos.")
        if not 0.0 <= self.food_regrowth_rate <= 1.0:
            raise ValueError("food_regrowth_rate debe estar entre cero y uno.")
        if any(value < 0.0 for value in (
            self.initial_energy,
            self.max_energy,
            self.movement_cost,
            self.hunger_cost,
            self.food_energy,
            self.hunt_energy_gain,
            self.reproduction_energy_threshold,
            self.reproduction_cost,
            self.rest_recovery_rate,
        )):
            raise ValueError("Los valores energeticos no pueden ser negativos.")
