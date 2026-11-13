"""Entrena y persiste las políticas neuronales sin iniciar la simulación."""

import argparse
import statistics
from pathlib import Path

from config import SimulationConfig
from learning.training import save_training_results, train_species_policies


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entrena las políticas neuronales del ecosistema."
    )
    parser.add_argument(
        "--output",
        default="checkpoints",
        help="Carpeta donde se guardarán latest.json y best.json.",
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--steps-per-episode", type=int, default=50)
    parser.add_argument("--evaluation-steps", type=int, default=50)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        help="Semillas independientes para reportar media y desviacion estandar.",
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Checkpoint desde el que se reanuda el entrenamiento.",
    )
    args = parser.parse_args()

    seeds = args.seeds or [0]
    rewards_by_species: dict[str, list[float]] = {}
    survival_by_species: dict[str, list[float]] = {}

    for seed in seeds:
        seed_output = (
            Path(args.output) / f"seed-{seed}"
            if len(seeds) > 1
            else Path(args.output)
        )
        _, reports = train_species_policies(
            config=SimulationConfig(seed=seed),
            epochs=args.epochs,
            episodes=args.episodes,
            steps_per_episode=args.steps_per_episode,
            evaluation_steps=args.evaluation_steps,
            gamma=args.gamma,
            checkpoint_dir=seed_output,
            resume_from=args.resume if len(seeds) == 1 else None,
            seed=seed,
        )
        # Al final de la ejecucion de cada semilla, se guardan los resultados de entrenamiento en 
        # un archivo JSON, para que puedan ser analizados posteriormente. 
        # Esto incluye métricas de rendimiento y supervivencia.
        save_training_results(
            seed,
            reports,
            seed_output / "training_results.json",
        )
        # Guardar los resultados de cada especie para calcular la media y desviación estándar
        for species, report in reports.items():
            rewards_by_species.setdefault(species.value, []).append(
                sum(report.rewards) / max(len(report.rewards), 1)
            )
            survival_by_species.setdefault(species.value, []).append(
                report.survival_rate
            )
    # Calcular y mostrar la media y desviación estándar de recompensa y supervivencia por especie
    for species in rewards_by_species:
        reward_values = rewards_by_species[species]
        survival_values = survival_by_species[species]
        # Calcular la desviación estándar de recompensa y supervivencia, 
        # manejando el caso de una sola semilla
        reward_spread = (
            statistics.stdev(reward_values)
            if len(reward_values) > 1
            else 0.0
        )
        # Calcular la desviación estándar de supervivencia, manejando el caso de una sola semilla
        survival_spread = (
            statistics.stdev(survival_values)
            if len(survival_values) > 1
            else 0.0
        )
        print(
            f"{species}: recompensa={statistics.mean(reward_values):.3f} "
            f"+/- {reward_spread:.3f}, "
            f"supervivencia={statistics.mean(survival_values):.3f} "
            f"+/- {survival_spread:.3f}"
        )
    print(f"Checkpoints guardados en {args.output}")


if __name__ == "__main__":
    main()
