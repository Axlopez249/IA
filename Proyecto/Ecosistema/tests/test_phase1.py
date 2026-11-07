import unittest

from agents.actions import Action
from agents.animal import Animal, Species
from config import SimulationConfig
from environment.resources import Food
from environment.world import World
from main import build_world
from metrics.collector import snapshot
from policies.rule_based import RuleBasedPolicy


class FixedPolicy:
    def __init__(self, action: Action) -> None:
        self.action = action

    def choose_action(self, animal: Animal, world: World) -> Action:
        return self.action


class Phase1Tests(unittest.TestCase):
    def test_world_is_reproducible_with_same_seed(self) -> None:
        # Comprueba que una misma semilla crea el mismo estado inicial.
        config = SimulationConfig(initial_food=4, initial_herbivores=2, initial_carnivores=1)
        first = build_world(config)
        second = build_world(config)
        self.assertEqual(snapshot(first), snapshot(second))
        self.assertEqual([(animal.x, animal.y) for animal in first.animals],
                         [(animal.x, animal.y) for animal in second.animals])

    def test_animal_eats_food_and_food_is_removed(self) -> None:
        # Comprueba que comer aumenta energia y elimina el recurso.
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
        # Comprueba que un animal sin energia se elimina del mundo.
        config = SimulationConfig(initial_energy=0, hunger_cost=0)
        world = World(config)
        animal = Animal(Species.HERBIVORE, 0, 0, 0, RuleBasedPolicy())
        world.add_animal(animal)

        world.step()

        self.assertFalse(animal.alive)
        self.assertEqual(world.animals, [])

    def test_move_consumes_energy_and_increases_age(self) -> None:
        config = SimulationConfig(width=3, height=3, hunger_cost=0.2, movement_cost=0.4)
        world = World(config)
        animal = Animal(
            Species.HERBIVORE,
            1,
            1,
            5,
            FixedPolicy(Action.MOVE),
        )
        world.add_animal(animal)

        world.step()

        self.assertEqual(animal.age, 1)
        self.assertEqual(animal.energy, 4.4)
        self.assertTrue(world.in_bounds(animal.x, animal.y))

    def test_animal_dies_at_maximum_age(self) -> None:
        config = SimulationConfig(max_age=1, hunger_cost=0)
        world = World(config)
        animal = Animal(
            Species.HERBIVORE,
            0,
            0,
            5,
            FixedPolicy(Action.REST),
        )
        world.add_animal(animal)

        world.step()

        self.assertFalse(animal.alive)
        self.assertEqual(world.animals, [])

    def test_move_at_single_cell_map_stays_inside_bounds(self) -> None:
        world = World(SimulationConfig(width=1, height=1, hunger_cost=0))
        animal = Animal(
            Species.HERBIVORE,
            0,
            0,
            5,
            FixedPolicy(Action.MOVE),
        )
        world.add_animal(animal)

        world.step()

        self.assertEqual((animal.x, animal.y), (0, 0))
        self.assertTrue(world.in_bounds(animal.x, animal.y))

    def test_food_regrows_on_an_empty_single_cell_map(self) -> None:
        world = World(
            SimulationConfig(
                width=1,
                height=1,
                initial_food=0,
                food_regrowth_rate=1.0,
            )
        )

        world.step()

        self.assertEqual(len(world.foods), 1)
        self.assertEqual((world.foods[0].x, world.foods[0].y), (0, 0))

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SimulationConfig(width=0)
        with self.assertRaises(ValueError):
            SimulationConfig(food_regrowth_rate=1.1)
        with self.assertRaises(ValueError):
            SimulationConfig(hunger_cost=-0.1)

    def test_energy_does_not_exceed_configured_maximum(self) -> None:
        config = SimulationConfig(max_energy=5, hunger_cost=0)
        world = World(config)
        animal = Animal(
            Species.HERBIVORE,
            0,
            0,
            4,
            FixedPolicy(Action.REST),
        )
        world.add_animal(animal)
        world.add_food(Food(0, 0, 4))

        animal.execute_action(Action.EAT, world)

        self.assertEqual(animal.energy, 5)


if __name__ == "__main__":
    unittest.main()