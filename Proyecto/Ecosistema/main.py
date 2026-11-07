# Punto de entrada para ejecutar una simulacion de la Fase 1.

import argparse

from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from metrics.collector import snapshot
from policies.neural import NeuralPolicy
from policies.rule_based import RuleBasedPolicy
from supervisors.base import Supervisor


def build_world(
	config: SimulationConfig | None = None,
	use_neural_policy: bool = False,
	supervisors: dict[Species, Supervisor] | None = None,
) -> World:
	# Crea un mundo con comida y poblaciones iniciales segun la configuracion.
	config = config or SimulationConfig()
	world = World(config, supervisors=supervisors or {})
	if use_neural_policy:
		herbivore_policy = NeuralPolicy(Species.HERBIVORE, seed=config.seed)
		carnivore_policy = NeuralPolicy(Species.CARNIVORE, seed=config.seed + 1)
	else:
		herbivore_policy = RuleBasedPolicy()
		carnivore_policy = herbivore_policy

	for _ in range(config.initial_food):
		x, y = world.random_position()
		world.add_food(Food(x, y, config.food_energy))
	for species, amount in (
		(Species.HERBIVORE, config.initial_herbivores),
		(Species.CARNIVORE, config.initial_carnivores),
	):
		policy = herbivore_policy if species == Species.HERBIVORE else carnivore_policy
		for _ in range(amount):
			x, y = world.random_position()
			world.add_animal(Animal(species, x, y, config.initial_energy, policy))
	return world


def run(
	steps: int | None = None,
	use_neural_policy: bool = False,
	visualize: bool = False,
	supervisors: dict[Species, Supervisor] | None = None,
) -> None:
	# Ejecuta la simulacion y muestra un resumen periodico de sus metricas.
	world = build_world(
		use_neural_policy=use_neural_policy,
		supervisors=supervisors,
	)
	total_steps = steps if steps is not None else world.config.max_steps
	if visualize:
		from visualization.visual import animate_world

		animate_world(world, total_steps, on_step=lambda current: print(snapshot(current)))
		return

	print(snapshot(world))
	for _ in range(total_steps):
		world.step()
		if world.step_count % 10 == 0 or not world.animals:
			print(snapshot(world))
		if not world.animals:
			break


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Ejecuta el simulador de ecosistema.")
	parser.add_argument("--visual", action="store_true", help="Abre la ventana 2D.")
	parser.add_argument("--neural", action="store_true", help="Usa politicas neuronales.")
	parser.add_argument("--steps", type=int, default=None, help="Numero de pasos.")
	args = parser.parse_args()
	run(
		steps=args.steps,
		use_neural_policy=args.neural,
		visualize=args.visual,
	)