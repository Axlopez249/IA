"""Agente de búsqueda para TileUp."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from EngineGame import GameEngine


class SearchAgent:
    """Esqueleto del agente de búsqueda."""

    def __init__(self, engine: "GameEngine", seed: int, time_limit: float):
        self.engine = engine
        self.seed = seed
        self.time_limit = time_limit
