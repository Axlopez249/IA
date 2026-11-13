# Entrenamiento supervisado y por refuerzo de las politicas del ecosistema.

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
from learning.rewards import calculate_reward
from policies.base import Policy
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


@dataclass
class ReinforceReport:
    # Resumen de un entrenamiento REINFORCE por episodios.

    rewards: list[float]
    episode_lengths: list[int]
    losses: list[float]
    survival_rate: float
    successes: list[int]


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
    successes: list[int] = []

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


def train_policy_reinforce(
    species: Species,
    config: SimulationConfig | None = None,
    episodes: int = 10,
    steps_per_episode: int = 50,
    gamma: float = 0.99,
    learning_rate: float = 0.01,
    seed: int = 0,
    policy: NeuralPolicy | None = None,
) -> tuple[NeuralPolicy, ReinforceReport]:
    # Entrena una politica mediante ensayo y error usando REINFORCE.
    # REINFORCE actualiza la politica despues de completar cada trayectoria.
    if episodes <= 0 or steps_per_episode <= 0:
        raise ValueError("episodes y steps_per_episode deben ser mayores que cero.")
    if not 0.0 < gamma <= 1.0:
        raise ValueError("gamma debe estar entre cero y uno.")
    if learning_rate <= 0.0:
        raise ValueError("learning_rate debe ser mayor que cero.")

    config = config or SimulationConfig()
    # La semilla mantiene reproducible la exploracion sin eliminar el azar.
    generator = random.Random(seed)
    # Al recibir una politica se conserva su aprendizaje entre epocas.
    trained_policy = policy or NeuralPolicy(species, seed=seed)
    episode_rewards: list[float] = []
    episode_lengths: list[int] = []
    losses: list[float] = []
    successes: list[int] = []
    survived_episodes = 0

    from learning.training_environment import IndividualTrainingEnvironment
    from main import build_world

    for episode in range(episodes):
        # Cada episodio empieza en un mundo nuevo para evitar reutilizar estados.
        episode_config = replace(
            config,
            seed=config.seed + seed + episode,
            max_steps=steps_per_episode,
        )
        opponent_species = (
            Species.CARNIVORE
            if species == Species.HERBIVORE
            else Species.HERBIVORE
        )
        world = build_world(
            episode_config,
            use_neural_policy=True,
            supervisors={},
            policies={
                species: trained_policy,
                opponent_species: NeuralPolicy(
                    opponent_species,
                    seed=seed + episode + 1,
                ),
            },
        )
        # Solo el animal seleccionado recibe las acciones de esta trayectoria.
        animal = next(
            (
                candidate
                for candidate in world.animals
                if candidate.species == species
            ),
            None,
        )
        if animal is None:
            raise RuntimeError(
                f"No se pudo crear un animal de la especie {species.value}."
            )

        environment = IndividualTrainingEnvironment(world, animal)
        observation = environment.reset()
        trajectory: list[tuple[tuple[float, ...], Action, float]] = []

        # La politica explora, observa la recompensa y guarda la trayectoria.
        for _ in range(steps_per_episode):
            action = _sample_policy_action(
                trained_policy,
                observation,
                generator,
            )
            result = environment.step(action)
            trajectory.append((observation, action, result.reward))
            observation = result.observation
            if result.done:
                break

        # G_t estima cuanto beneficio futuro produjo cada decision.
        returns = _discounted_returns(
            [reward for _, _, reward in trajectory],
            gamma,
        )
        total_loss = 0.0
        # El gradiente refuerza acciones con retornos altos y castiga las demas.
        for (state, action, _), return_value in zip(trajectory, returns):
            total_loss += trained_policy.network.train_policy_gradient(
                state,
                action_index(action),
                return_value,
                learning_rate,
                valid_action_indices=[
                    action_index(valid_action)
                    for valid_action in trained_policy.valid_actions()
                ],
            )

        episode_rewards.append(round(sum(reward for _, _, reward in trajectory), 4))
        episode_lengths.append(len(trajectory))
        losses.append(total_loss / max(len(trajectory), 1))
        if animal.alive:
            survived_episodes += 1
            successes.append(1)
        else:
            successes.append(0)

    return trained_policy, ReinforceReport(
        rewards=episode_rewards,
        episode_lengths=episode_lengths,
        losses=losses,
        survival_rate=survived_episodes / episodes,
        successes=successes,
    )


def _sample_policy_action(
    policy: NeuralPolicy,
    observation: tuple[float, ...],
    generator: random.Random,
) -> Action:
    # Muestrea una accion valida segun la distribucion de la politica.
    valid_actions = policy.valid_actions()
    logits = policy.network.forward(observation)
    # Se excluyen acciones imposibles antes de convertir logits a probabilidades.
    valid_logits = [
        logits[action_index(action)]
        for action in valid_actions
    ]
    probabilities = policy.network.softmax(valid_logits)
    threshold = generator.random()
    cumulative = 0.0
    # La accion se elige con muestreo categorico, no con argmax.
    for action, probability in zip(valid_actions, probabilities):
        cumulative += probability
        if threshold <= cumulative:
            return action
    return valid_actions[-1]


def _discounted_returns(rewards: list[float], gamma: float) -> list[float]:
    # Calcula G_t = r_t + gamma*r_(t+1) + ... para una trayectoria.
    returns = [0.0] * len(rewards)
    running_return = 0.0
    # Se recorre hacia atras porque cada retorno depende del siguiente.
    for index in range(len(rewards) - 1, -1, -1):
        running_return = rewards[index] + gamma * running_return
        returns[index] = running_return
    return returns


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
) -> tuple[dict[Species, NeuralPolicy], dict[Species, ReinforceReport]]:
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
    gamma = float(training_options.pop("gamma", 0.99))
    if training_options:
        unknown = ", ".join(sorted(training_options))
        raise TypeError(f"Opciones de entrenamiento desconocidas: {unknown}")

    checkpoint_dir = Path(checkpoint_dir_value) if checkpoint_dir_value else None
    # Las politicas cargadas permiten continuar el aprendizaje desde latest.json.
    policies = _load_or_create_training_policies(resume_from, seed)
    reports = {
        species: ReinforceReport([], [], [], 0.0, [])
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
        # Cada epoca acumula nuevas trayectorias para ambas especies.
        for offset, species in enumerate((Species.HERBIVORE, Species.CARNIVORE)):
            policy, report = train_policy_reinforce(
                species,
                config=config,
                episodes=episodes,
                steps_per_episode=steps_per_episode,
                gamma=gamma,
                learning_rate=learning_rate,
                seed=seed + epoch + offset,
                policy=policies[species],
            )
            policies[species] = policy
            reports[species].rewards.extend(report.rewards)
            reports[species].episode_lengths.extend(report.episode_lengths)
            reports[species].losses.extend(report.losses)
            reports[species].successes.extend(report.successes)
            reports[species].survival_rate = report.survival_rate

        # La evaluacion no entrena; solo decide si el checkpoint merece ser best.
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
                    "reward": reports[species].rewards[-1]
                    if reports[species].rewards
                    else None,
                    "survival_rate": reports[species].survival_rate,
                }
                for species in reports
            },
        }
        if checkpoint_dir:
            # latest siempre representa el estado mas reciente del entrenamiento.
            save_species_policies(
                policies,
                checkpoint_dir / "latest.json",
                metadata=metadata,
            )
            if fitness > best_fitness:
                # best conserva el estado con mejor desempeno ecologico observado.
                best_fitness = fitness
                save_species_policies(
                    policies,
                    checkpoint_dir / "best.json",
                    metadata=metadata,
                )

    return policies, reports


def evaluate_policies(
    policies: dict[Species, Policy],
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
    tracked_animal = world.animals[0] if world.animals else None
    episode_reward = 0.0
    for _ in range(steps):
        if not world.animals:
            break
        previous_energy = (
            tracked_animal.energy if tracked_animal is not None else 0.0
        )
        was_alive = tracked_animal.alive if tracked_animal is not None else False
        previous_births = world.births
        previous_hunts = world.hunts
        world.step()
        if tracked_animal is not None:
            action = world.last_actions.get(
                tracked_animal.identifier,
                Action.REST,
            )
            episode_reward += calculate_reward(
                tracked_animal,
                action,
                previous_energy,
                was_alive,
                previous_hunts,
                previous_births,
                world,
            )

        # El agente evaluado es un individuo representativo del episodio.
        # El fitness sigue midiendo el estado global del ecosistema.
        if tracked_animal is not None and not tracked_animal.alive:
            break

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
        "episode_reward": round(episode_reward, 4),
        "episode_length": world.step_count,
        "fitness": round(fitness, 6),
    }
    return round(fitness, 6), evaluation


def save_training_results(
    seed: int,
    reports: dict[Species, ReinforceReport],
    path: str | Path,
) -> None:
    """Guarda las series por episodio para generar curvas entre semillas."""
    payload = {
        "seed": seed,
        "species": {
            species.value: {
                "rewards": report.rewards,
                "episode_lengths": report.episode_lengths,
                "losses": report.losses,
                "survival_rate": report.survival_rate,
                "successes": report.successes,
            }
            for species, report in reports.items()
        },
    }
    results_path = Path(path)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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