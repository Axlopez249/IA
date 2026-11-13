"""Entrena y persiste las políticas neuronales sin iniciar la simulación."""

import argparse

from config import SimulationConfig
from learning.training import train_species_policies


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
        "--resume",
        default=None,
        help="Checkpoint desde el que se reanuda el entrenamiento.",
    )
    args = parser.parse_args()

    policies, reports = train_species_policies(
        epochs=args.epochs,
        episodes=args.episodes,
        steps_per_episode=args.steps_per_episode,
        evaluation_steps=args.evaluation_steps,
        gamma=args.gamma,
        checkpoint_dir=args.output,
        resume_from=args.resume,
    )
    for species, report in reports.items():
        print(
            f"{species.value}: episodios={len(report.rewards)}, "
            f"recompensa_promedio={sum(report.rewards) / max(len(report.rewards), 1):.3f}, "
            f"supervivencia={report.survival_rate:.3f}"
        )
    print(f"Checkpoints guardados en {args.output}")


if __name__ == "__main__":
    main()
