# Entrenamiento supervisado por imitacion de la politica basada en reglas.

from __future__ import annotations

import random
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from agents.actions import Action
from agents.animal import Species
from config import SimulationConfig
from learning.network import NeuralNetwork
from learning.observations import OBSERVATION_SIZE, build_observation
from policies.neural import NeuralPolicy
from policies.rule_based import RuleBasedPolicy


@dataclass
class TrainingExample:
    # Una observacion y la accion que queremos que la red imite.

    observation: tuple[float, ...]
    action: Action


@dataclass
class TrainingReport:
    # Resumen de un entrenamiento completo.

    losses: list[float]
    accuracy: float
    examples: int


POLICY_FILE_VERSION = 1
CHECKPOINT_VERSION = 1


def action_index(action: Action) -> int:
    # Convierte el enum de accion en la posicion usada por la salida de la red.
    return list(Action).index(action)


def collect_examples(
    species: Species,
    config: SimulationConfig,
    episodes: int = 5,
    steps_per_episode: int = 50,
) -> list[TrainingExample]:
    # Ejecuta mundos con reglas y guarda decisiones como datos de entrenamiento.
    examples: list[TrainingExample] = []
    teacher = RuleBasedPolicy()
    from main import build_world

    for episode in range(episodes):
        # Cada episodio usa una semilla diferente para generar situaciones variadas.
        episode_config = replace(config, seed=config.seed + episode)
        world = build_world(episode_config)

        for _ in range(steps_per_episode):
            world.update_objectives()
            for animal in list(world.animals):
                if not animal.alive or animal.species != species:
                    continue

                animal.objective = world.objectives.get(animal.species)
                observation = build_observation(animal, world)
                action = teacher.choose_action(animal, world)
                examples.append(TrainingExample(observation, action))

            world.step()
            if not world.animals:
                break

    return examples


def calculate_accuracy(
    network: NeuralNetwork,
    examples: list[TrainingExample],
) -> float:
    # Mide cuantas acciones de entrenamiento reproduce la red correctamente.
    if not examples:
        return 0.0

    correct = 0
    for example in examples:
        logits = network.forward(example.observation)
        predicted_index = logits.index(max(logits))
        if predicted_index == action_index(example.action):
            correct += 1
    return correct / len(examples)


def train_network(
    network: NeuralNetwork,
    examples: list[TrainingExample],
    epochs: int = 10,
    learning_rate: float = 0.01,
    seed: int = 0,
) -> list[float]:
    # Entrena la red varias veces sobre los ejemplos en orden aleatorio.
    if not examples:
        return []

    generator = random.Random(seed)
    losses: list[float] = []

    for _ in range(epochs):
        shuffled_examples = list(examples)
        generator.shuffle(shuffled_examples)
        total_loss = 0.0

        for example in shuffled_examples:
            total_loss += network.train_supervised(
                example.observation,
                action_index(example.action),
                learning_rate,
            )

        losses.append(total_loss / len(shuffled_examples))

    return losses


def train_species_policy(
    species: Species,
    config: SimulationConfig | None = None,
    episodes: int = 5,
    steps_per_episode: int = 50,
    epochs: int = 10,
    learning_rate: float = 0.01,
    seed: int = 0,
) -> tuple[NeuralPolicy, TrainingReport]:
    # Crea ejemplos, entrena una red y devuelve una politica lista para evaluar.
    config = config or SimulationConfig()
    examples = collect_examples(species, config, episodes, steps_per_episode)
    network = NeuralNetwork(OBSERVATION_SIZE, seed=seed)
    losses = train_network(network, examples, epochs, learning_rate, seed)
    policy = NeuralPolicy(species, network=network, seed=seed)
    accuracy = calculate_accuracy(network, examples)
    return policy, TrainingReport(losses, accuracy, len(examples))


def save_species_policies(
    policies: dict[Species, NeuralPolicy],
    path: str | Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Guarda las redes y el contexto necesario para inspeccionar el entrenamiento."""
    expected_species = {Species.HERBIVORE, Species.CARNIVORE}
    if set(policies) != expected_species:
        raise ValueError("Se requieren políticas para herbívoros y carnívoros.")

    payload: dict[str, Any] = {
        "version": POLICY_FILE_VERSION,
        "policies": {
            species.value: {
                "exploration_rate": policies[species].exploration_rate,
                "network": policies[species].network.to_dict(),
            }
            for species in expected_species
        },
    }
    if metadata is not None:
        payload["metadata"] = metadata

    policy_path = Path(path)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def load_species_policies(path: str | Path) -> dict[Species, NeuralPolicy]:
    """Carga políticas persistidas sin volver a entrenarlas."""
    policy_path = Path(path)
    if not policy_path.is_file():
        raise FileNotFoundError(f"No existe el archivo de políticas: {policy_path}")

    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if payload.get("version") != POLICY_FILE_VERSION:
        raise ValueError("La versión del archivo de políticas no es compatible.")

    stored_policies = payload.get("policies")
    if not isinstance(stored_policies, dict):
        raise ValueError("El archivo de políticas no contiene políticas válidas.")

    policies: dict[Species, NeuralPolicy] = {}
    for species in (Species.HERBIVORE, Species.CARNIVORE):
        stored = stored_policies.get(species.value)
        if not isinstance(stored, dict):
            raise ValueError(f"Falta la política de {species.value}.")
        policies[species] = NeuralPolicy(
            species,
            network=NeuralNetwork.from_dict(stored["network"]),
            exploration_rate=float(stored.get("exploration_rate", 0.0)),
        )
    return policies


def train_species_policies(
    config: SimulationConfig | None = None,
    **training_options: Any,
) -> tuple[dict[Species, NeuralPolicy], dict[Species, TrainingReport]]:
    """Entrena ambas especies y devuelve políticas listas para persistir.

    Cuando se indica ``checkpoint_dir``, cada época se evalúa en una simulación
    independiente. Así podemos conservar la última versión y, por separado,
    la versión que produjo el mejor comportamiento ecológico observado.
    """
    config = config or SimulationConfig()
    episodes = int(training_options.pop("episodes", 5))
    steps_per_episode = int(training_options.pop("steps_per_episode", 50))
    epochs = int(training_options.pop("epochs", 10))
    learning_rate = float(training_options.pop("learning_rate", 0.01))
    seed = int(training_options.pop("seed", 0))
    checkpoint_dir_value = training_options.pop("checkpoint_dir", None)
    evaluation_steps = int(training_options.pop("evaluation_steps", 50))
    resume_from = training_options.pop("resume_from", None)
    if training_options:
        unknown = ", ".join(sorted(training_options))
        raise TypeError(f"Opciones de entrenamiento desconocidas: {unknown}")

    checkpoint_dir = Path(checkpoint_dir_value) if checkpoint_dir_value else None
    policies = _load_or_create_training_policies(resume_from, seed)
    examples = {
        species: collect_examples(
            species,
            config,
            episodes=episodes,
            steps_per_episode=steps_per_episode,
        )
        for species in (Species.HERBIVORE, Species.CARNIVORE)
    }
    reports = {
        species: TrainingReport([], 0.0, len(examples[species]))
        for species in (Species.HERBIVORE, Species.CARNIVORE)
    }

    start_epoch = 0
    best_fitness = float("-inf")
    if resume_from is not None:
        resume_metadata = _load_checkpoint_metadata(resume_from)
        start_epoch = int(resume_metadata.get("epoch", 0))
        best_path = Path(resume_from).with_name("best.json")
        if best_path.is_file():
            best_metadata = _load_checkpoint_metadata(best_path)
            best_fitness = float(best_metadata.get("fitness", best_fitness))
    if checkpoint_dir:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(start_epoch + 1, start_epoch + epochs + 1):
        for offset, species in enumerate((Species.HERBIVORE, Species.CARNIVORE)):
            losses = train_network(
                policies[species].network,
                examples[species],
                epochs=1,
                learning_rate=learning_rate,
                seed=seed + epoch + offset,
            )
            reports[species].losses.extend(losses)
            reports[species].accuracy = calculate_accuracy(
                policies[species].network,
                examples[species],
            )

        fitness, evaluation = evaluate_policies(
            policies,
            config,
            steps=evaluation_steps,
        )
        metadata = {
            "checkpoint_version": CHECKPOINT_VERSION,
            "epoch": epoch,
            "fitness": fitness,
            "evaluation": evaluation,
            "reports": {
                species.value: {
                    "loss": reports[species].losses[-1]
                    if reports[species].losses
                    else None,
                    "accuracy": reports[species].accuracy,
                    "examples": reports[species].examples,
                }
                for species in reports
            },
        }
        if checkpoint_dir:
            save_species_policies(
                policies,
                checkpoint_dir / "latest.json",
                metadata=metadata,
            )
            if fitness > best_fitness:
                best_fitness = fitness
                save_species_policies(
                    policies,
                    checkpoint_dir / "best.json",
                    metadata=metadata,
                )

    return policies, reports


def evaluate_policies(
    policies: dict[Species, NeuralPolicy],
    config: SimulationConfig,
    steps: int = 50,
) -> tuple[float, dict[str, int | float]]:
    """Evalúa una pareja de políticas sin modificar el mundo de entrenamiento.

    La puntuación prioriza conservar individuos y energía, pero también reconoce
    una población estable, nacimientos y cacerías. Las métricas se devuelven
    junto con la puntuación para que cada checkpoint sea auditable.
    """
    from main import build_world

    evaluation_config = replace(
        config,
        seed=config.seed + 100_000,
        max_steps=steps,
    )
    world = build_world(
        evaluation_config,
        use_neural_policy=True,
        policies=policies,
    )
    initial_population = len(world.animals)
    for _ in range(steps):
        if not world.animals:
            break
        world.step()

    current_population = len(world.animals)
    survival = current_population / max(initial_population, 1)
    average_energy = (
        sum(animal.energy for animal in world.animals)
        / max(current_population, 1)
        / max(config.max_energy, 1.0)
    )
    population_stability = min(
        current_population / max(initial_population, 1),
        1.0,
    )
    normalized_births = min(world.births / max(initial_population, 1), 1.0)
    normalized_hunts = min(world.hunts / max(initial_population, 1), 1.0)
    fitness = (
        0.40 * survival
        + 0.25 * min(average_energy, 1.0)
        + 0.20 * population_stability
        + 0.10 * normalized_births
        + 0.05 * normalized_hunts
    )
    evaluation = {
        "animals": current_population,
        "births": world.births,
        "deaths": world.deaths,
        "hunts": world.hunts,
        "average_energy": round(
            sum(animal.energy for animal in world.animals)
            / max(current_population, 1),
            4,
        ),
        "survival": round(survival, 4),
    }
    return round(fitness, 6), evaluation


def _load_or_create_training_policies(
    resume_from: str | Path | None,
    seed: int,
) -> dict[Species, NeuralPolicy]:
    if resume_from is not None:
        return load_species_policies(resume_from)
    return {
        Species.HERBIVORE: NeuralPolicy(Species.HERBIVORE, seed=seed),
        Species.CARNIVORE: NeuralPolicy(Species.CARNIVORE, seed=seed + 1),
    }


def _load_checkpoint_metadata(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"El checkpoint no contiene metadatos: {path}")
    return metadata