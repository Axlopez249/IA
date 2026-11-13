# Punto de entrada para ejecutar una simulacion de la Fase 1.

import argparse
from pathlib import Path

from agents.animal import Animal, Species, Variation
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from learning.training import load_species_policies, save_species_policies
from metrics.collector import snapshot
from policies.base import Policy
from policies.neural import NeuralPolicy
from policies.rule_based import RuleBasedPolicy
from supervisors.base import Supervisor, RuleBasedSupervisor


def build_world(
	config: SimulationConfig | None = None,
	use_neural_policy: bool = False,
	supervisors: dict[Species, Supervisor] | None = None,
	policies: dict[Species, Policy] | None = None,
) -> World:
	# Crea un mundo con comida y poblaciones iniciales segun la configuracion.
	config = config or SimulationConfig()
	world = World(config, supervisors=supervisors or {})
	# Usa politicas neuronales persistidas o redes nuevas si se solicita.
	if use_neural_policy:
		if policies is None:
			herbivore_policy = NeuralPolicy(Species.HERBIVORE, seed=config.seed)
			carnivore_policy = NeuralPolicy(Species.CARNIVORE, seed=config.seed + 1)
		else:
			herbivore_policy = policies[Species.HERBIVORE]
			carnivore_policy = policies[Species.CARNIVORE]
	else:
		herbivore_policy = RuleBasedPolicy()
		carnivore_policy = herbivore_policy
		
	for _ in range(config.initial_food):
		x, y = world.random_position()
		world.add_food(Food(x, y, config.food_energy))
		
	for _ in range(config.initial_herbivores):
		x, y = world.random_position()
		var = world.rng.choice([Variation.H_NORMAL, Variation.H_FAST, Variation.H_SLOW])
		world.add_animal(Animal(Species.HERBIVORE, x, y, config.initial_energy, herbivore_policy, variation=var))
		
	for _ in range(config.initial_carnivores):
		x, y = world.random_position()
		var = world.rng.choice([Variation.C_RESISTANT, Variation.C_FAST])
		world.add_animal(Animal(Species.CARNIVORE, x, y, config.initial_energy, carnivore_policy, variation=var))

	return world


def run(
	steps: int | None = None,
	use_neural_policy: bool = False,
	visualize: bool = False,
	supervisors: dict[Species, Supervisor] | None = None,
	policies: dict[Species, Policy] | None = None,
	save_policy_file: str | Path | None = None,
) -> None:

	#Inteligencia de enjambre
	if supervisors is None:
		supervisors = (
			{}
			if use_neural_policy
			else {
				Species.HERBIVORE: RuleBasedSupervisor(Species.HERBIVORE),
				Species.CARNIVORE: RuleBasedSupervisor(Species.CARNIVORE)
			}
		)

	# Ejecuta la simulacion y muestra un resumen periodico de sus metricas.
	world = build_world(
		use_neural_policy=use_neural_policy,
		supervisors=supervisors,
		policies=policies,
	)
	effective_policies = policies
	if use_neural_policy and effective_policies is None:
		herbivore = next(
			(animal for animal in world.animals if animal.species == Species.HERBIVORE),
			None,
		)
		carnivore = next(
			(animal for animal in world.animals if animal.species == Species.CARNIVORE),
			None,
		)
		if herbivore is not None and carnivore is not None:
			effective_policies = {
				Species.HERBIVORE: herbivore.policy,
				Species.CARNIVORE: carnivore.policy,
			}
	total_steps = steps if steps is not None else world.config.max_steps
	try:
		if visualize:
			from visualization.visual import animate_world

			animate_world(
				world,
				total_steps,
				on_step=lambda current: print(snapshot(current)),
			)
			return

		print(snapshot(world))
		for _ in range(total_steps):
			world.step()
			if world.step_count % 10 == 0 or not world.animals:
				print(snapshot(world))
			if not world.animals:
				break
	finally:
		if save_policy_file and effective_policies:
			save_species_policies(
				effective_policies,
				save_policy_file,
				metadata={
					"source": "simulation",
					"step": world.step_count,
					"snapshot": snapshot(world),
				},
			)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Ejecuta el simulador de ecosistema.")
	parser.add_argument("--visual", action="store_true", help="Abre la ventana 2D.")
	parser.add_argument("--neural", action="store_true", help="Usa politicas neuronales.")
	parser.add_argument(
		"--resume",
		action="store_true",
		help="Carga checkpoints/latest.json para continuar con los pesos actuales.",
	)
	parser.add_argument(
		"--load",
		choices=("best",),
		default=None,
		help="Carga el checkpoint best.json para una demostracion sin exploracion.",
	)
	parser.add_argument(
		"--policy-file",
		default=None,
		help="Carga pesos neuronales persistidos desde un archivo JSON.",
	)
	parser.add_argument(
		"--save-policy-file",
		default=None,
		help="Guarda los pesos usados al finalizar la simulación.",
	)
	parser.add_argument("--steps", type=int, default=None, help="Numero de pasos.")
	args = parser.parse_args()
	if args.resume and args.load is not None:
		parser.error("--resume y --load best no se pueden usar juntos.")

	policy_file = args.policy_file
	if args.resume:
		policy_file = str(Path("checkpoints") / "latest.json")
	elif args.load == "best":
		policy_file = str(Path("checkpoints") / "best.json")

	if policy_file is not None:
		args.neural = True
	policies = load_species_policies(policy_file) if policy_file else None
	if args.load == "best" and policies is not None:
		for policy in policies.values():
			policy.exploration_rate = 0.0
	save_policy_file = args.save_policy_file
	if args.neural and save_policy_file is None and args.load != "best":
		save_policy_file = str(Path("checkpoints") / "latest.json")
	run(
		steps=args.steps,
		use_neural_policy=args.neural,
		visualize=args.visual,
		policies=policies,
		save_policy_file=save_policy_file,
	)