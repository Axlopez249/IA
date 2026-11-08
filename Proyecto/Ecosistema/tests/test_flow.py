import unittest

from agents.actions import Action
from agents.animal import Animal, Species
from config import SimulationConfig
from environment.world import World
from learning.training_environment import IndividualTrainingEnvironment
from policies.rule_based import RuleBasedPolicy
from supervisors.base import RuleBasedSupervisor
from supervisors.objectives import Objective


class FixedPolicy:
    def __init__(self, action: Action) -> None:
        self.action = action

    def choose_action(self, animal: Animal, world: World) -> Action:
        return self.action


class CountingSupervisor:
    def __init__(self, objective: Objective) -> None:
        self.objective = objective
        self.calls = 0

    def choose_objective(self, world: World) -> Objective:
        self.calls += 1
        return self.objective


class FlowTests(unittest.TestCase):
    def test_reproduction_cost_is_applied_once_when_resolved(self) -> None:
        config = SimulationConfig(
            width=3,
            height=3,
            initial_energy=5,
            reproduction_age=1,
            reproduction_energy_threshold=5,
            reproduction_cost=3,
            hunger_cost=0,
            max_herbivores=10,
            food_regrowth_rate=0,
        )
        world = World(config)
        first = Animal(
            Species.HERBIVORE,
            1,
            1,
            5,
            FixedPolicy(Action.REPRODUCE),
            age=1,
        )
        second = Animal(
            Species.HERBIVORE,
            1,
            1,
            5,
            FixedPolicy(Action.REPRODUCE),
            age=1,
        )
        world.add_animal(first)
        world.add_animal(second)

        world.step()

        self.assertEqual(world.births, 1)
        self.assertEqual(first.energy, 2)
        self.assertEqual(second.energy, 2)

    def test_reproduction_queue_rejects_ineligible_pair_at_resolution(self) -> None:
        config = SimulationConfig(
            reproduction_age=5,
            reproduction_energy_threshold=10,
            initial_energy=5,
            max_herbivores=10,
        )
        world = World(config)
        first = Animal(Species.HERBIVORE, 0, 0, 5, FixedPolicy(Action.REST))
        second = Animal(Species.HERBIVORE, 0, 0, 5, FixedPolicy(Action.REST))
        world.add_animal(first)
        world.add_animal(second)
        world.queue_reproduction(first)
        world.queue_reproduction(second)

        world.resolve_reproduction()

        self.assertEqual(world.births, 0)
        self.assertEqual(len(world.animals), 2)
        self.assertEqual(first.energy, 5)
        self.assertEqual(second.energy, 5)

    def test_supervisor_can_direct_eligible_population_to_reproduce(self) -> None:
        config = SimulationConfig(
            width=3,
            height=3,
            initial_energy=10,
            reproduction_age=1,
            reproduction_energy_threshold=10,
            reproduction_cost=1,
            hunger_cost=0,
            min_herbivores=0,
            max_herbivores=10,
            food_regrowth_rate=0,
        )
        supervisor = RuleBasedSupervisor(Species.HERBIVORE)
        world = World(
            config,
            supervisors={Species.HERBIVORE: supervisor},
        )
        first = Animal(Species.HERBIVORE, 1, 1, 10, RuleBasedPolicy(), age=1)
        second = Animal(Species.HERBIVORE, 1, 1, 10, RuleBasedPolicy(), age=1)
        world.add_animal(first)
        world.add_animal(second)

        world.step()

        self.assertEqual(world.births, 1)
        self.assertEqual(first.objective, Objective.GROUP)

    def test_training_environment_updates_objective_before_action(self) -> None:
        supervisor = CountingSupervisor(Objective.SURVIVE)
        world = World(
            SimulationConfig(food_regrowth_rate=0),
            supervisors={Species.HERBIVORE: supervisor},
        )
        animal = Animal(Species.HERBIVORE, 0, 0, 10, FixedPolicy(Action.REST))
        world.add_animal(animal)

        environment = IndividualTrainingEnvironment(world, animal)
        environment.step(Action.REST)

        self.assertEqual(supervisor.calls, 1)
        self.assertEqual(animal.objective, Objective.SURVIVE)

    def test_configuration_rejects_inconsistent_energy_and_population_limits(self) -> None:
        with self.assertRaises(ValueError):
            SimulationConfig(max_energy=-1)
        with self.assertRaises(ValueError):
            SimulationConfig(hunt_energy=-1)
        with self.assertRaises(ValueError):
            SimulationConfig(rest_energy_threshold=-1)


if __name__ == "__main__":
    unittest.main()
