"""Compara los baselines y una política entrenada con el mismo protocolo."""

from __future__ import annotations

import argparse
import statistics
from dataclasses import replace
from pathlib import Path

from agents.animal import Species
from config import SimulationConfig
from learning.training import evaluate_policies, load_species_policies
from policies.random import RandomPolicy
from policies.rule_based import RuleBasedPolicy


def _policy_set(kind: str, seed: int, checkpoint: Path | None):
    if kind == "random":
        return {
            Species.HERBIVORE: RandomPolicy(Species.HERBIVORE, seed),
            Species.CARNIVORE: RandomPolicy(Species.CARNIVORE, seed + 1),
        }
    if kind == "heuristic":
        return {
            Species.HERBIVORE: RuleBasedPolicy(),
            Species.CARNIVORE: RuleBasedPolicy(),
        }
    if checkpoint is None:
        raise ValueError("Se necesita un checkpoint para evaluar neural.")
    return load_species_policies(checkpoint)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compara baselines y REINFORCE con varias semillas."
    )
    parser.add_argument("--checkpoints", default="checkpoints")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    args = parser.parse_args()

    # Evaluar cada política con cada semilla y recopilar métricas
    for kind in ("random", "heuristic", "neural"):
        # Inicializar listas para almacenar métricas de cada semilla
        fitness_values: list[float] = []
        success_values: list[float] = []
        reward_values: list[float] = []
        length_values: list[float] = []

        # Se recorre cada semilla y se evalúa la política correspondiente
        for seed in args.seeds:
            # constryuir el checkpoint para la política neural si es necesario
            checkpoint = (
                Path(args.checkpoints) / f"seed-{seed}" / "best.json"
                if kind == "neural"
                else None
            )
            # Se establecen las políticas para cada especie según el tipo de política (random, heuristic, neural)
            policies = _policy_set(kind, seed, checkpoint)
            # Se evalúan las políticas y se obtienen métricas de fitness, éxito, recompensa y longitud del episodio
            fitness, evaluation = evaluate_policies(
                policies,
                replace(SimulationConfig(seed=seed), max_steps=args.steps),
                steps=args.steps,
            )
            # Se almacenan las métricas obtenidas en las listas correspondientes
            fitness_values.append(fitness)
            success_values.append(float(evaluation["survival"]))
            reward_values.append(float(evaluation["episode_reward"]))
            length_values.append(float(evaluation["episode_length"]))

        # Se imprimen las métricas promedio y la desviación estándar para cada tipo de política
        print(
            f"{kind}: fitness={statistics.mean(fitness_values):.3f} "
            f"+/- {statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0.0:.3f}, "
            f"exito={statistics.mean(success_values):.3f} "
            f"+/- {statistics.stdev(success_values) if len(success_values) > 1 else 0.0:.3f}, "
            f"recompensa={statistics.mean(reward_values):.3f} "
            f"+/- {statistics.stdev(reward_values) if len(reward_values) > 1 else 0.0:.3f}, "
            f"longitud={statistics.mean(length_values):.1f}"
        )


if __name__ == "__main__":
    main()
