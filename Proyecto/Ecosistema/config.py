# Configuracion central de la simulacion.

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
	# Parametros de la simulacion, agrupados para facilitar experimentos.

	width: int = 30
	height: int = 20
	initial_herbivores: int = 8
	initial_carnivores: int = 3
	initial_food: int = 45
	food_regrowth_rate: float = 0.08
	initial_energy: float = 12.0
	max_energy: float = 20.0
	movement_cost: float = 0.4
	hunger_cost: float = 0.2
	food_energy: float = 4.0
	max_steps: int = 100
	seed: int = 7
	hunt_energy: float = 7.0
	reproduction_energy_threshold: float = 10.0
	reproduction_age: int = 5
	reproduction_cost: float = 3.0
	max_age: int = 300
	perception_radius: int = 5
	rest_energy_threshold: float = 18.0

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
			self.hunt_energy,
			self.reproduction_energy_threshold,
			self.reproduction_cost,
			self.rest_energy_threshold,
		)):
			raise ValueError("Los valores energeticos no pueden ser negativos.")
