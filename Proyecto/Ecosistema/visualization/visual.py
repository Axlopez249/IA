"""Visualizacion grafica 2D  """

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Callable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

if TYPE_CHECKING:
    from environment.world import World


def animate_world(
    world: "World",
    steps: int | None = None,
    interval: int = 250,
    on_step: Callable[["World"], None] | None = None,
) -> FuncAnimation:
    """Muestra el mundo en una ventana y avanza la simulacion paso a paso."""
    total_steps = steps if steps is not None else world.config.max_steps
    figure, axis = plt.subplots(figsize=(10, 6))
    figure.subplots_adjust(top=0.88)
    axis.set_xlim(-0.5, world.config.width - 0.5)
    axis.set_ylim(-0.5, world.config.height - 0.5)
    axis.set_aspect("equal")
    axis.set_xlabel("x")
    axis.set_ylabel("y")
    axis.grid(alpha=0.2)

    food_plot = axis.scatter([], [], marker="s", color="gold", label="Comida")
    herbivore_plot = axis.scatter(
        [], [], color="forestgreen", label="Herbivoros"
    )
    carnivore_plot = axis.scatter([], [], color="firebrick", label="Carnivoros")
    axis.legend(loc="upper right")
    herbivore_counter = figure.text(
        0.02,
        0.96,
        "",
        color="forestgreen",
        fontweight="bold",
    )
    carnivore_counter = figure.text(
        0.22,
        0.96,
        "",
        color="firebrick",
        fontweight="bold",
    )
    status_text = figure.text(0.5, 0.96, "", ha="center")
    position_labels: list[object] = []

    def update(frame: int) -> tuple[object, ...]:
        nonlocal position_labels

        if frame > 0 and world.animals:
            world.step()
        if on_step is not None and (
            frame == 0
            or world.step_count % 10 == 0
            or not world.animals
        ):
            on_step(world)

        food_positions = [(food.x, food.y) for food in world.foods]
        herbivore_positions = [
            (animal.x, animal.y)
            for animal in world.animals
            if animal.species.value == "herbivore"
        ]
        carnivore_positions = [
            (animal.x, animal.y)
            for animal in world.animals
            if animal.species.value == "carnivore"
        ]
        food_plot.set_offsets(_positions(food_positions))
        herbivore_plot.set_offsets(_positions(herbivore_positions))
        carnivore_plot.set_offsets(_positions(carnivore_positions))
        herbivore_counter.set_text(f"Herbivoros: {len(herbivore_positions)}")
        carnivore_counter.set_text(f"Carnivoros: {len(carnivore_positions)}")
        for label in position_labels:
            label.remove()
        position_labels = []
        herbivore_counts = Counter(herbivore_positions)
        carnivore_counts = Counter(carnivore_positions)
        occupied_positions = set(herbivore_counts) | set(carnivore_counts)
        for position in occupied_positions:
            labels = []
            if herbivore_counts[position] > 1:
                labels.append(f"H{herbivore_counts[position]}")
            if carnivore_counts[position] > 1:
                labels.append(f"C{carnivore_counts[position]}")
            if labels:
                position_labels.append(
                    axis.text(
                        position[0],
                        position[1],
                        "/".join(labels),
                        color="white",
                        ha="center",
                        va="center",
                        fontsize=8,
                        fontweight="bold",
                        bbox={"facecolor": "black", "alpha": 0.7, "pad": 1},
                    )
                )
        status_text.set_text(
            f"Paso {world.step_count} | "
            f"Animales: {len(world.animals)} | "
            f"Muertes: {world.deaths}"
        )
        return (
            food_plot,
            herbivore_plot,
            carnivore_plot,
            herbivore_counter,
            carnivore_counter,
            status_text,
            *position_labels,
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=total_steps + 1,
        interval=interval,
        repeat=False,
        blit=False,
    )
    plt.show()
    return animation


def _positions(positions: list[tuple[int, int]]) -> np.ndarray:
    if not positions:
        return np.empty((0, 2))
    return np.asarray(positions)
