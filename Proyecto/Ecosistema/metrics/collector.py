# Lecturas pequenas del estado del mundo.
from __future__ import annotations
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from environment.world import World

def snapshot(world: "World") -> dict[str, int | float]:
    species_count = Counter(animal.species.value for animal in world.animals)
    h_count = species_count["herbivore"]
    c_count = species_count["carnivore"]
    
    h_energy = sum(a.energy for a in world.animals if a.species.value == "herbivore") / (h_count if h_count else 1)
    c_energy = sum(a.energy for a in world.animals if a.species.value == "carnivore") / (c_count if c_count else 1)

    return {
        "step": world.step_count,
        "animals": len(world.animals),
        "herbivores": h_count,
        "carnivores": c_count,
        "food": len(world.foods),
        "total_energy": round(sum(animal.energy for animal in world.animals), 2),
        "avg_energy_h": round(h_energy, 2),
        "avg_energy_c": round(c_energy, 2),
        "births": world.births,
        "deaths": world.deaths,
        "hunts": world.hunts,
    }