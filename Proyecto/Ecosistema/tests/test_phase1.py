import unittest

from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from main import build_world
from metrics.collector import snapshot
from policies.rule_based import RuleBasedPolicy


class Phase1Tests(unittest.TestCase):
    def test_world_is_reproducible_with_same_seed(self) -> None:
        config = SimulationConfig(initial_food=4, initial_herbivores=2, initial_carnivores=1)
        first = build_world(config)
        second = build_world(config)
        self.assertEqual(snapshot(first), snapshot(second))
        self.assertEqual([(animal.x, animal.y) for animal in first.animals],
                         [(animal.x, animal.y) for animal in second.animals])

    def test_animal_eats_food_and_food_is_removed(self) -> None:
        config = SimulationConfig(width=3, height=3, initial_energy=2, hunger_cost=0)
        world = World(config)
        animal = Animal(Species.HERBIVORE, 1, 1, 2, RuleBasedPolicy())
        world.add_animal(animal)
        world.add_food(Food(1, 1, 4))

        world.step()

        self.assertEqual(len(world.foods), 0)
        self.assertEqual(animal.energy, 6)
        self.assertTrue(animal.alive)

    def test_animal_dies_when_energy_reaches_zero(self) -> None:
        config = SimulationConfig(initial_energy=0, hunger_cost=0)
        world = World(config)
        animal = Animal(Species.HERBIVORE, 0, 0, 0, RuleBasedPolicy())
        world.add_animal(animal)

        world.step()

        self.assertFalse(animal.alive)
        self.assertEqual(world.animals, [])


if __name__ == "__main__":
    unittest.main()