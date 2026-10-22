"""Politica determinista minima para la Fase 1."""

from __future__ import annotations


class RuleBasedPolicy:
    """Come si hay comida en la casilla; en otro caso se mueve."""

    def choose_action(self, animal: "Animal", world: "World") -> str:
        if world.food_at(animal.x, animal.y) is not None:
            return "eat"
        return "move"
