import unittest

from agents.animal import Animal, Species
from config import SimulationConfig
from environment.world import World
from policies.rule_based import RuleBasedPolicy


class Phase2Tests(unittest.TestCase):
    def make_world(self) -> World:
        # Crea un mundo pequeno sin regeneracion para pruebas deterministas.
        return World(SimulationConfig(width=8, height=8, food_regrowth_rate=0))

    def test_carnivore_hunts_herbivore_on_same_cell(self) -> None:
        # Comprueba que una caceria elimina a la presa y actualiza metricas.
        world = self.make_world()
        carnivore = Animal(Species.CARNIVORE, 3, 3, 5, RuleBasedPolicy())
        herbivore = Animal(Species.HERBIVORE, 3, 3, 5, RuleBasedPolicy())
        world.add_animal(carnivore)
        world.add_animal(herbivore)

        world.step()

        self.assertEqual(len(world.animals), 1)
        self.assertIs(world.animals[0], carnivore)
        self.assertEqual(world.hunts, 1)
        self.assertEqual(world.deaths, 1)

    def test_herbivore_flees_from_nearby_predator(self) -> None:
        # Comprueba que un herbivoro se aleja de un depredador cercano.
        world = self.make_world()
        herbivore = Animal(Species.HERBIVORE, 3, 3, 5, RuleBasedPolicy())
        predator = Animal(Species.CARNIVORE, 4, 3, 5, RuleBasedPolicy())
        world.add_animal(herbivore)
        world.add_animal(predator)

        world.step()

        self.assertEqual((herbivore.x, herbivore.y), (2, 3))

    def test_far_away_predator_is_not_perceived(self) -> None:
        # Comprueba que la percepcion respeta el radio configurado.
        world = self.make_world()
        herbivore = Animal(Species.HERBIVORE, 0, 0, 5, RuleBasedPolicy())
        predator = Animal(Species.CARNIVORE, 7, 7, 5, RuleBasedPolicy())
        world.add_animal(herbivore)
        world.add_animal(predator)

        self.assertIsNone(world.nearest_predator(herbivore))

    def test_two_eligible_animals_create_one_child(self) -> None:
        # Comprueba que una pareja compatible crea una sola cria.
        config = SimulationConfig(
            width=8,
            height=8,
            food_regrowth_rate=0,
            reproduction_age=1,
            reproduction_energy_threshold=5,
            initial_energy=5,
            reproduction_cost=0,
            hunger_cost=0,
        )
        world = World(config)
        first = Animal(Species.HERBIVORE, 2, 2, 5, RuleBasedPolicy(), age=1)
        second = Animal(Species.HERBIVORE, 2, 2, 5, RuleBasedPolicy(), age=1)
        world.add_animal(first)
        world.add_animal(second)

        world.step()

        self.assertEqual(len(world.animals), 3)
        self.assertEqual(world.births, 1)


if __name__ == "__main__":
    unittest.main()