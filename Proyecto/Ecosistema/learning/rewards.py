# Calcula recompensas sencillas para el futuro aprendizaje por refuerzo.

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.actions import Action

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


def calculate_reward(
    animal: "Animal",
    action: Action,
    previous_energy: float,
    was_alive: bool,
    previous_hunts: int,
    previous_births: int,
    world: "World",
) -> float:
    # Usa cambios observables del entorno para crear una recompensa explicable.
    reward = animal.energy - previous_energy

    if animal.alive:
        reward += 0.05
    elif was_alive:
        reward -= 10.0

    reward += (world.hunts - previous_hunts) * 3.0
    reward += (world.births - previous_births) * 2.0

    # Mantiene la variable action en la interfaz para poder ajustar recompensas
    # especificas por accion en la siguiente etapa de entrenamiento.
    if action == Action.REST and animal.alive:
        reward += 0.02

    return round(reward, 4)