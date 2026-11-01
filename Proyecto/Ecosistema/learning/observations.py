# Convierte el estado del mundo en entradas numericas para la red neuronal.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


# Todas las politicas neuronales deben recibir vectores de este tamano.
OBSERVATION_SIZE = 20


def limit(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    # Mantiene un valor dentro de un intervalo estable para la red.
    return max(minimum, min(value, maximum))


def describe_target(animal: "Animal", target: object | None, radius: int) -> tuple[float, float, float]:
    # Devuelve distancia normalizada y direccion relativa de un objetivo.
    if target is None:
        return 1.0, 0.0, 0.0

    target_x = getattr(target, "x")
    target_y = getattr(target, "y")
    distance = abs(animal.x - target_x) + abs(animal.y - target_y)
    horizontal = (target_x - animal.x) / max(radius, 1)
    vertical = (target_y - animal.y) / max(radius, 1)
    normalized_distance = distance / max(radius, 1)
    return (
        limit(normalized_distance, 0.0, 1.0),
        limit(horizontal),
        limit(vertical),
    )


def count_nearby_animals(animal: "Animal", world: "World", same_species: bool) -> int:
    # Cuenta animales vivos dentro del radio de percepcion.
    count = 0
    for candidate in world.animals:
        if candidate is animal or not candidate.alive:
            continue
        if same_species and candidate.species != animal.species:
            continue
        if not same_species and candidate.species == animal.species:
            continue
        if world.distance(animal, candidate) <= world.config.perception_radius:
            count += 1
    return count


def count_visible_food(animal: "Animal", world: "World") -> int:
    # Cuenta comida que el animal puede percibir.
    return sum(
        world.distance(animal, food) <= world.config.perception_radius
        for food in world.foods
    )


def build_observation(animal: "Animal", world: "World") -> tuple[float, ...]:
    # Construye una observacion local, normalizada y de tamano fijo.
    radius = world.config.perception_radius
    maximum_energy = max(world.config.max_energy, 1.0)
    maximum_age = max(world.config.max_age, 1)

    food_distance, food_dx, food_dy = describe_target(
        animal,
        world.nearest_food(animal) if animal.species.value == "herbivore" else None,
        radius,
    )
    predator_distance, predator_dx, predator_dy = describe_target(
        animal,
        world.nearest_predator(animal),
        radius,
    )
    prey_distance, prey_dx, prey_dy = describe_target(
        animal,
        world.nearest_prey(animal) if animal.species.value == "carnivore" else None,
        radius,
    )

    width = max(world.config.width - 1, 1)
    height = max(world.config.height - 1, 1)
    observation = (
        limit(animal.energy / maximum_energy, 0.0, 1.0),
        limit(animal.age / maximum_age, 0.0, 1.0),
        food_distance,
        food_dx,
        food_dy,
        predator_distance,
        predator_dx,
        predator_dy,
        prey_distance,
        prey_dx,
        prey_dy,
        limit(count_nearby_animals(animal, world, True) / 10.0, 0.0, 1.0),
        limit(count_nearby_animals(animal, world, False) / 10.0, 0.0, 1.0),
        limit(count_visible_food(animal, world) / 10.0, 0.0, 1.0),
        animal.x / width,
        (world.config.width - 1 - animal.x) / width,
        animal.y / height,
        (world.config.height - 1 - animal.y) / height,
        1.0 if animal.species.value == "herbivore" else 0.0,
        1.0 if animal.species.value == "carnivore" else 0.0,
    )
    # Las direcciones necesitan conservar signos negativos y positivos.
    return tuple(limit(value, -1.0, 1.0) for value in observation)