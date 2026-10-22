"""Configuracion central de la simulacion."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
	"""Parametros de la Fase 1, agrupados para facilitar experimentos."""

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
