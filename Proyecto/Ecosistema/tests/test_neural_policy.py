import unittest

from agents.actions import Action
from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from learning.network import NeuralNetwork
from learning.observations import OBSERVATION_SIZE, build_observation
from learning.training import TrainingExample, action_index, train_network
from main import build_world
from policies.neural import NeuralPolicy


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

    def test_training_reduces_loss_for_a_repeated_example(self) -> None:
        network = NeuralNetwork(OBSERVATION_SIZE, seed=4)
        observation = tuple(0.5 for _ in range(OBSERVATION_SIZE))
        examples = [TrainingExample(observation, Action.MOVE)]

        losses = train_network(network, examples, epochs=10, learning_rate=0.1)

        self.assertEqual(action_index(Action.MOVE), 0)
        self.assertLess(losses[-1], losses[0])


if __name__ == "__main__":
    unittest.main()