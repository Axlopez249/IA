import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.actions import Action
from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from learning.network import NeuralNetwork
from learning.observations import OBSERVATION_SIZE, build_observation
from learning.training import (
    TrainingExample,
    action_index,
    load_species_policies,
    save_species_policies,
    train_species_policies,
    train_network,
)
from main import build_world
from policies.neural import NeuralPolicy
from policies.random import RandomPolicy


class NeuralPolicyTests(unittest.TestCase):
    def test_observation_has_fixed_size_and_normalized_values(self) -> None:
        config = SimulationConfig(width=5, height=5, food_regrowth_rate=0)
        world = World(config)
        animal = Animal(Species.HERBIVORE, 2, 2, 10, NeuralPolicy(Species.HERBIVORE))
        world.add_animal(animal)
        world.add_food(Food(2, 3))

        observation = build_observation(animal, world)

        self.assertEqual(len(observation), OBSERVATION_SIZE)
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in observation))

    def test_network_produces_one_logit_per_action(self) -> None:
        network = NeuralNetwork(OBSERVATION_SIZE, seed=3)

        logits = network.forward(tuple(0.5 for _ in range(OBSERVATION_SIZE)))

        self.assertEqual(len(logits), 6)

    def test_neural_policy_selects_valid_actions(self) -> None:
        world = build_world(use_neural_policy=True)
        herbivore = next(animal for animal in world.animals if animal.species == Species.HERBIVORE)
        carnivore = next(animal for animal in world.animals if animal.species == Species.CARNIVORE)

        herbivore_action = herbivore.policy.choose_action(herbivore, world)
        carnivore_action = carnivore.policy.choose_action(carnivore, world)

        self.assertIn(herbivore_action, herbivore.policy.valid_actions())
        self.assertIn(carnivore_action, carnivore.policy.valid_actions())

    def test_random_policy_selects_only_valid_actions(self) -> None:
        world = build_world()
        for species in (Species.HERBIVORE, Species.CARNIVORE):
            policy = RandomPolicy(species, seed=3)
            animal = next(
                animal for animal in world.animals if animal.species == species
            )
            self.assertIn(policy.choose_action(animal, world), policy.valid_actions())

    def test_policy_gradient_accepts_only_valid_actions(self) -> None:
        network = NeuralNetwork(OBSERVATION_SIZE, seed=5)
        network.train_policy_gradient(
            tuple(0.0 for _ in range(OBSERVATION_SIZE)),
            action_index(Action.EAT),
            1.0,
            valid_action_indices=[
                action_index(action)
                for action in NeuralPolicy(Species.HERBIVORE).valid_actions()
            ],
        )
        with self.assertRaises(ValueError):
            network.train_policy_gradient(
                tuple(0.0 for _ in range(OBSERVATION_SIZE)),
                action_index(Action.HUNT),
                1.0,
                valid_action_indices=[
                    action_index(action)
                    for action in NeuralPolicy(Species.HERBIVORE).valid_actions()
                ],
            )

    def test_training_reduces_loss_for_a_repeated_example(self) -> None:
        network = NeuralNetwork(OBSERVATION_SIZE, seed=4)
        observation = tuple(0.5 for _ in range(OBSERVATION_SIZE))
        examples = [TrainingExample(observation, Action.MOVE)]

        losses = train_network(network, examples, epochs=10, learning_rate=0.1)

        self.assertEqual(action_index(Action.MOVE), 0)
        self.assertLess(losses[-1], losses[0])

    def test_persisted_policies_keep_network_predictions(self) -> None:
        policies = {
            Species.HERBIVORE: NeuralPolicy(Species.HERBIVORE, seed=10),
            Species.CARNIVORE: NeuralPolicy(Species.CARNIVORE, seed=11),
        }
        observation = tuple(0.25 for _ in range(OBSERVATION_SIZE))
        expected = {
            species: policy.network.forward(observation)
            for species, policy in policies.items()
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "policies.json"
            save_species_policies(policies, path)
            loaded = load_species_policies(path)

        for species in policies:
            self.assertEqual(
                loaded[species].network.forward(observation),
                expected[species],
            )

    def test_training_saves_latest_and_best_checkpoints_with_fitness(self) -> None:
        config = SimulationConfig(
            width=4,
            height=4,
            initial_herbivores=2,
            initial_carnivores=1,
            initial_food=2,
            food_regrowth_rate=0,
            max_steps=2,
        )

        with TemporaryDirectory() as directory:
            policies, reports = train_species_policies(
                config,
                episodes=1,
                steps_per_episode=1,
                epochs=2,
                evaluation_steps=1,
                checkpoint_dir=directory,
                seed=2,
            )
            latest = Path(directory) / "latest.json"
            best = Path(directory) / "best.json"
            latest_payload = latest.read_text(encoding="utf-8")
            best_payload = best.read_text(encoding="utf-8")

        self.assertTrue(policies)
        self.assertTrue(reports[Species.HERBIVORE].losses)
        self.assertIn('"metadata"', latest_payload)
        self.assertIn('"fitness"', latest_payload)
        self.assertIn('"metadata"', best_payload)


if __name__ == "__main__":
    unittest.main()