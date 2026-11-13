"""Ejecuta el protocolo de Etapa 2 y guarda tablas y curvas reproducibles."""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from dataclasses import replace
from pathlib import Path

from agents.animal import Species
from config import SimulationConfig
from learning.training import (
    evaluate_policies,
    load_species_policies,
    train_species_policies,
)
from policies.random import RandomPolicy
from policies.rule_based import RuleBasedPolicy


def _policy_set(kind: str, seed: int, checkpoint: Path | None):
    """Construye la política que se evaluará con una semilla concreta."""
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
        raise ValueError(f"No existe checkpoint para la semilla {seed}.")
    return load_species_policies(checkpoint)


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    """Escribe una tabla de métricas para que pueda usarse en el artículo."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _plot_training(path: Path, rows: list[dict[str, object]]) -> None:
    """Genera curvas de entrenamiento con bandas de desviación estándar."""
    import matplotlib.pyplot as plt

    metrics = (
        ("reward", "Recompensa acumulada"),
        ("episode_length", "Longitud del episodio"),
        ("success", "Tasa de éxito"),
    )
    figure, axes = plt.subplots(1, 3, figsize=(18, 5))
    for axis, (metric, title) in zip(axes, metrics):
        for species in ("herbivore", "carnivore"):
            grouped: dict[int, list[float]] = {}
            for row in rows:
                if row["species"] != species:
                    continue
                episode = int(row["episode"])
                grouped.setdefault(episode, []).append(float(row[metric]))
            episodes = sorted(grouped)
            means = [statistics.mean(grouped[episode]) for episode in episodes]
            spreads = [
                statistics.stdev(grouped[episode])
                if len(grouped[episode]) > 1
                else 0.0
                for episode in episodes
            ]
            label = "Herbívoros" if species == "herbivore" else "Carnívoros"
            axis.plot(episodes, means, label=label)
            axis.fill_between(
                episodes,
                [mean - spread for mean, spread in zip(means, spreads)],
                [mean + spread for mean, spread in zip(means, spreads)],
                alpha=0.2,
            )
        axis.set_title(title)
        axis.set_xlabel("Episodio")
        axis.grid(alpha=0.25)
        axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _plot_evaluation(path: Path, rows: list[dict[str, object]]) -> None:
    """Genera la comparación final de políticas con barras de error."""
    import matplotlib.pyplot as plt

    metrics = (
        ("reward", "Recompensa"),
        ("success", "Éxito"),
        ("episode_length", "Longitud"),
    )
    kinds = ("random", "heuristic", "neural")
    labels = ("Aleatoria", "Heurística", "REINFORCE")
    figure, axes = plt.subplots(1, 3, figsize=(15, 5))
    for axis, (metric, title) in zip(axes, metrics):
        means = []
        spreads = []
        for kind in kinds:
            values = [float(row[metric]) for row in rows if row["policy"] == kind]
            means.append(statistics.mean(values))
            spreads.append(statistics.stdev(values) if len(values) > 1 else 0.0)
        axis.bar(labels, means, yerr=spreads, capsize=4)
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.25)
        axis.tick_params(axis="x", rotation=20)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main() -> None:
    """Ejecuta entrenamiento, evaluación y generación de todos los artefactos."""
    parser = argparse.ArgumentParser(
        description="Genera resultados reproducibles de la Etapa 2."
    )
    parser.add_argument("--output", default="experiments/stage2")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--steps-per-episode", type=int, default=50)
    parser.add_argument("--evaluation-steps", type=int, default=50)
    parser.add_argument("--evaluation-episodes", type=int, default=10)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    args = parser.parse_args()

    output = Path(args.output)
    checkpoints = output / "checkpoints"
    output.mkdir(parents=True, exist_ok=True)
    training_rows: list[dict[str, object]] = []
    start = time.perf_counter()
    total_training_episodes = args.epochs * args.episodes

    print("=== Protocolo experimental de la Etapa 2 ===", flush=True)
    print(f"Semillas: {args.seeds}", flush=True)
    print(
        f"Episodios por especie y semilla: {total_training_episodes} "
        f"({args.epochs} épocas x {args.episodes} episodios)",
        flush=True,
    )
    print(
        f"Evaluación: {args.evaluation_episodes} episodios x "
        f"{len(args.seeds)} semillas por política",
        flush=True,
    )
    print(f"Salida: {output.resolve()}", flush=True)

    for seed in args.seeds:
        seed_start = time.perf_counter()
        print(f"\n[ENTRENAMIENTO] Semilla {seed}: iniciando", flush=True)
        _, reports = train_species_policies(
            config=SimulationConfig(seed=seed),
            epochs=args.epochs,
            episodes=args.episodes,
            steps_per_episode=args.steps_per_episode,
            evaluation_steps=args.evaluation_steps,
            gamma=args.gamma,
            learning_rate=args.learning_rate,
            checkpoint_dir=checkpoints / f"seed-{seed}",
            seed=seed,
        )
        print(
            f"[ENTRENAMIENTO] Semilla {seed}: completada en "
            f"{time.perf_counter() - seed_start:.1f}s",
            flush=True,
        )
        for species, report in reports.items():
            print(
                f"  {species.value}: {len(report.rewards)} episodios, "
                f"recompensa media "
                f"{statistics.mean(report.rewards):.3f}, "
                f"éxito {report.survival_rate:.3f}",
                flush=True,
            )
            for episode, (reward, length, loss, survived) in enumerate(
                zip(
                    report.rewards,
                    report.episode_lengths,
                    report.losses,
                    report.successes,
                ),
                start=1,
            ):
                training_rows.append(
                    {
                        "seed": seed,
                        "species": species.value,
                        "episode": episode,
                        "reward": reward,
                        "episode_length": length,
                        "loss": loss,
                        "success": int(survived),
                    }
                )

    _write_rows(
        output / "training_metrics.csv",
        ["seed", "species", "episode", "reward", "episode_length", "loss", "success"],
        training_rows,
    )
    print(
        f"[ARCHIVOS] Guardado training_metrics.csv ({len(training_rows)} filas)",
        flush=True,
    )
    evaluation_rows: list[dict[str, object]] = []
    for kind in ("random", "heuristic", "neural"):
        print(f"\n[EVALUACIÓN] Política {kind}", flush=True)
        for seed in args.seeds:
            checkpoint = (
                checkpoints / f"seed-{seed}" / "best.json"
                if kind == "neural"
                else None
            )
            policies = _policy_set(kind, seed, checkpoint)
            print(
                f"  Semilla {seed}: {args.evaluation_episodes} episodios",
                flush=True,
            )
            for evaluation_episode in range(1, args.evaluation_episodes + 1):
                _, evaluation = evaluate_policies(
                    policies,
                    replace(
                        SimulationConfig(seed=seed + evaluation_episode),
                        max_steps=args.evaluation_steps,
                    ),
                    steps=args.evaluation_steps,
                )
                evaluation_rows.append(
                    {
                        "policy": kind,
                        "seed": seed,
                        "evaluation_episode": evaluation_episode,
                        "fitness": evaluation.get("fitness", 0.0),
                        "reward": evaluation["episode_reward"],
                        "success": evaluation["survival"],
                        "episode_length": evaluation["episode_length"],
                    }
                )

    _write_rows(
        output / "evaluation_metrics.csv",
        [
            "policy",
            "seed",
            "evaluation_episode",
            "fitness",
            "reward",
            "success",
            "episode_length",
        ],
        evaluation_rows,
    )
    print(
        f"[ARCHIVOS] Guardado evaluation_metrics.csv "
        f"({len(evaluation_rows)} filas)",
        flush=True,
    )
    print("[GRÁFICAS] Generando training_curves.png", flush=True)
    _plot_training(output / "training_curves.png", training_rows)
    print("[GRÁFICAS] Generando evaluation_comparison.png", flush=True)
    _plot_evaluation(output / "evaluation_comparison.png", evaluation_rows)
    elapsed = time.perf_counter() - start
    (output / "run_metadata.txt").write_text(
        f"seeds={args.seeds}\n"
        f"epochs={args.epochs}\n"
        f"episodes_per_epoch={args.episodes}\n"
        f"steps_per_episode={args.steps_per_episode}\n"
        f"evaluation_episodes={args.evaluation_episodes}\n"
        f"gamma={args.gamma}\n"
        f"learning_rate={args.learning_rate}\n"
        f"elapsed_seconds={elapsed:.3f}\n",
        encoding="utf-8",
    )
    print(
        f"\n[FINALIZADO] Resultados guardados en {output} "
        f"en {elapsed:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
