import unittest

from agents.animal import Animal, Species
from config import SimulationConfig
from environment.world import World
from policies.rule_based import RuleBasedPolicy
from supervisors.objectives import Objective


class FixedSupervisor:
    def __init__(self, objective: Objective) -> None:
        self.objective = objective
        self.calls = 0

    def choose_objective(self, world: World) -> Objective:
        self.calls += 1
        return self.objective


class ExtensibilityTests(unittest.TestCase):
    def test_supervisor_objective_is_optional_and_shared_by_species(self) -> None:
        supervisor = FixedSupervisor(Objective.SEARCH_FOOD)
        world = World(
            SimulationConfig(width=4, height=4, food_regrowth_rate=0),
            supervisors={Species.HERBIVORE: supervisor},
        )
        first = Animal(Species.HERBIVORE, 0, 0, 5, RuleBasedPolicy())
        second = Animal(Species.HERBIVORE, 1, 1, 5, RuleBasedPolicy())
        world.add_animal(first)
        world.add_animal(second)

        world.step()

        self.assertEqual(supervisor.calls, 1)
        self.assertEqual(first.objective, Objective.SEARCH_FOOD)
        self.assertEqual(second.objective, Objective.SEARCH_FOOD)

if __name__ == "__main__":
    unittest.main()