# Punto de entrada para ejecutar una simulacion de la Fase 1.

from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from metrics.collector import snapshot
from policies.rule_based import RuleBasedPolicy


def build_world(config: SimulationConfig | None = None) -> World:
	# Crea un mundo con comida y poblaciones iniciales segun la configuracion.
	config = config or SimulationConfig()
	world = World(config)
	policy = RuleBasedPolicy()

	for _ in range(config.initial_food):
		x, y = world.random_position()
		world.add_food(Food(x, y, config.food_energy))
	for species, amount in (
		(Species.HERBIVORE, config.initial_herbivores),
		(Species.CARNIVORE, config.initial_carnivores),
	):
		for _ in range(amount):
			x, y = world.random_position()
			world.add_animal(Animal(species, x, y, config.initial_energy, policy))
	return world


def run(steps: int | None = None) -> None:
	# Ejecuta la simulacion y muestra un resumen periodico de sus metricas.
	world = build_world()
	total_steps = steps if steps is not None else world.config.max_steps
	print(snapshot(world))
	for _ in range(total_steps):
		world.step()
		if world.step_count % 10 == 0 or not world.animals:
			print(snapshot(world))
		if not world.animals:
			break


if __name__ == "__main__":
	run()