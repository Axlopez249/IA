"""Agente evolutivo para TileUp."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from EngineGame import GameEngine


class EvolutionaryAgent:
    """Esqueleto del agente evolutivo."""

    def __init__(self, engine: "GameEngine", seed: int, time_limit: float):
        self.engine = engine
        self.seed = seed
        self.time_limit = time_limit
