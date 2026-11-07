# Politica individual que utiliza una red neuronal compartida por especie.

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from agents.actions import Action
from agents.animal import Species
from learning.network import NeuralNetwork
from learning.observations import OBSERVATION_SIZE, build_observation
from supervisors.base import action_for_objective

if TYPE_CHECKING:
    from agents.animal import Animal
    from environment.world import World


class NeuralPolicy:
    # Convierte observaciones locales en acciones validas para una especie.

    def __init__(
        self,
        species: Species,
        network: NeuralNetwork | None = None,
        seed: int = 0,
        exploration_rate: float = 0.0,
    ) -> None:
        # La red puede compartirse entre todos los animales de una especie.
        self.species = species
        self.network = network or NeuralNetwork(OBSERVATION_SIZE, seed=seed)
        self.exploration_rate = exploration_rate
        self.random = random.Random(seed)

    def valid_actions(self) -> tuple[Action, ...]:
        # Impide que una especie seleccione acciones que no puede ejecutar.
        if self.species == Species.HERBIVORE:
            return (
                Action.MOVE,
                Action.EAT,
                Action.FLEE,
                Action.REST,
                Action.REPRODUCE,
            )
        return (
            Action.MOVE,
            Action.HUNT,
            Action.FLEE,
            Action.REST,
            Action.REPRODUCE,
        )

    def choose_action(self, animal: "Animal", world: "World") -> Action:
        supervised_action = action_for_objective(animal, world)
        if supervised_action is not None:
            return supervised_action

        # Observa el mundo, calcula logits y selecciona una accion valida.
        observation = build_observation(animal, world)
        logits = self.network.forward(observation)
        actions = list(Action)
        valid_actions = self.valid_actions()

        if self.random.random() < self.exploration_rate:
            return self.random.choice(valid_actions)

        # Filtra los logits para solo incluir los correspondientes a acciones validas.
        valid_logits = [
            (logit, action)
            for logit, action in zip(logits, actions)
            if action in valid_actions
        ]
        return max(valid_logits, key=lambda item: item[0])[1]