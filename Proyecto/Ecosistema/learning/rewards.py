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
    # Se normaliza el cambio de energia para que REST no domine la recompensa
    # solo porque recupera varios puntos en una unica accion.
    energy_change = animal.energy - previous_energy
    energy_scale = max(
        world.config.food_energy,
        world.config.hunt_energy_gain,
        1.0,
    )
    reward = energy_change / energy_scale

    if animal.alive:
        reward += 0.05
    elif was_alive:
        reward -= 10.0

    hunts = world.hunts - previous_hunts
    births = world.births - previous_births
    reward += hunts * 3.0
    reward += births * 2.0

    # Descansar es una herramienta de recuperacion, no el objetivo principal.
    # Solo se premia cuando el animal realmente tiene energia baja; con energia
    # suficiente se penaliza para evitar que aprenda a descansar indefinidamente.
    if action == Action.REST and animal.alive:
        if previous_energy < world.config.rest_energy_threshold:
            reward += 0.15
        else:
            reward -= 0.30

    # La reproduccion tiene un coste alto. La bonificacion adicional compensa
    # parte de ese coste unicamente cuando la solicitud produjo una cria.
    if action == Action.REPRODUCE and births > 0:
        reward += 5.0

    return round(reward, 4)