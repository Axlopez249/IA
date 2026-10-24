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
