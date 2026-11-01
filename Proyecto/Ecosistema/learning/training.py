# Entrenamiento supervisado por imitacion de la politica basada en reglas.

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from agents.actions import Action
from agents.animal import Species
from config import SimulationConfig
from learning.network import NeuralNetwork
from learning.observations import OBSERVATION_SIZE, build_observation
from main import build_world
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

    for episode in range(episodes):
        # Cada episodio usa una semilla diferente para generar situaciones variadas.
        episode_config = replace(config, seed=config.seed + episode)
        world = build_world(episode_config)

        for _ in range(steps_per_episode):
            for animal in list(world.animals):
                if not animal.alive or animal.species != species:
                    continue

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