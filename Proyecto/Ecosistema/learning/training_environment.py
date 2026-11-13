# Entorno minimo para probar una politica individual antes de usar PPO.

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.actions import Action
from learning.observations import build_observation
from learning.rewards import calculate_reward

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


@dataclass
class StepResult:
    # Resultado de una accion dentro del entorno de entrenamiento.

    observation: tuple[float, ...]
    reward: float
    done: bool
    action: Action


class IndividualTrainingEnvironment:
    # Ejecuta acciones de un individuo y conserva el resto del mundo simple.

    def __init__(self, world: "World", animal: "Animal") -> None:
        # El animal recibido es el individuo que controla el entrenador.
        self.world = world
        self.animal = animal

    def reset(self) -> tuple[float, ...]:
        # Devuelve la observacion inicial del episodio actual.
        # El entrenador crea un mundo nuevo antes de cada episodio.
        return build_observation(self.animal, self.world)

    def step(self, action: Action) -> StepResult:
        # Ejecuta una accion y avanza el mundo un tick.
        previous_energy = self.animal.energy
        was_alive = self.animal.alive
        previous_hunts = self.world.hunts
        previous_births = self.world.births

        # El entorno no usa la politica de reglas para elegir la accion controlada.
        self.world.update_objectives()
        self.animal.objective = self.world.objectives.get(self.animal.species)
        if self.animal.alive:
            self.animal.execute_action(action, self.world)

        self.world.resolve_reproduction()
        if was_alive and not self.animal.alive:
            self.world.deaths += 1
        self.world.regrow_food()
        self.world.animals = [
            candidate for candidate in self.world.animals if candidate.alive
        ]
        self.world.step_count += 1

        reward = calculate_reward(
            self.animal,
            action,
            previous_energy,
            was_alive,
            previous_hunts,
            previous_births,
            self.world,
        )
        done = not self.animal.alive or self.world.step_count >= self.world.config.max_steps
        return StepResult(
            observation=build_observation(self.animal, self.world),
            reward=reward,
            done=done,
            action=action,
        )