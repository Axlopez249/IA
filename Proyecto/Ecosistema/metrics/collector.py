# Lecturas pequenas del estado del mundo.

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from environment.world import World


def snapshot(world: "World") -> dict[str, int | float]:
    # Devuelve un resumen serializable del estado actual del mundo.
    species = Counter(animal.species.value for animal in world.animals)
    return {
        "step": world.step_count,
        "animals": len(world.animals),
        "herbivores": species["herbivore"],
        "carnivores": species["carnivore"],
        "food": len(world.foods),
        "total_energy": round(sum(animal.energy for animal in world.animals), 2),
        "births": world.births,
        "deaths": world.deaths,
        "hunts": world.hunts,
    }
