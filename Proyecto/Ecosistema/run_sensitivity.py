"""Ejecuta el estudio de sensibilidad de la tasa de aprendizaje."""

from __future__ import annotations

import argparse
import csv
import statistics
import subprocess
import sys
from pathlib import Path


def _mean_by_seed(
    rows: list[dict[str, str]],
    metric: str,
) -> list[tuple[int, float]]:
    by_seed: dict[int, list[float]] = {}
    for row in rows:
        by_seed.setdefault(int(row["seed"]), []).append(float(row[metric]))
    return [
        (seed, statistics.mean(values))
        for seed, values in sorted(by_seed.items())
    ]


def _write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "learning_rate",
        "seed",
        "fitness",
        "reward",
        "success",
        "episode_length",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _plot_summary(path: Path, rows: list[dict[str, object]]) -> None:
    import matplotlib.pyplot as plt

    metrics = (
        ("fitness", "Fitness"),
        ("reward", "Recompensa"),
        ("success", "Éxito"),
        ("episode_length", "Longitud"),
    )
    rates = sorted({float(row["learning_rate"]) for row in rows})
    figure, axes = plt.subplots(1, 4, figsize=(18, 5))
    for axis, (metric, title) in zip(axes, metrics):
        means = []
        spreads = []
        for rate in rates:
            values = [
                float(row[metric])
                for row in rows
                if float(row["learning_rate"]) == rate
            ]
            means.append(statistics.mean(values))
            spreads.append(statistics.stdev(values) if len(values) > 1 else 0.0)
        axis.errorbar(rates, means, yerr=spreads, marker="o", capsize=4)
        axis.set_title(title)
        axis.set_xlabel("Tasa de aprendizaje")
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compara varias tasas de aprendizaje con las mismas semillas."
    )
    parser.add_argument("--output", default="experiments/sensitivity")
    parser.add_argument(
        "--learning-rates",
        type=float,
        nargs="+",
        default=[0.005, 0.01, 0.02],
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--steps-per-episode", type=int, default=50)
    parser.add_argument("--evaluation-steps", type=int, default=50)
    parser.add_argument("--evaluation-episodes", type=int, default=10)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, object]] = []
    script = Path(__file__).with_name("run_experiments.py")

    for rate in args.learning_rates:
        rate_name = format(rate, "g")
        run_output = output / f"learning-rate-{rate_name}"
        command = [
            sys.executable,
            str(script),
            "--output",
            str(run_output),
            "--epochs",
            str(args.epochs),
            "--episodes",
            str(args.episodes),
            "--steps-per-episode",
            str(args.steps_per_episode),
            "--evaluation-steps",
            str(args.evaluation_steps),
            "--evaluation-episodes",
            str(args.evaluation_episodes),
            "--gamma",
            str(args.gamma),
            "--learning-rate",
            str(rate),
            "--seeds",
            *(str(seed) for seed in args.seeds),
        ]
        print(f"\n=== Tasa de aprendizaje: {rate} ===", flush=True)
        subprocess.run(command, check=True)

        evaluation_path = run_output / "evaluation_metrics.csv"
        with evaluation_path.open(encoding="utf-8") as file:
            evaluation_rows = list(csv.DictReader(file))
        neural_rows = [
            row for row in evaluation_rows if row["policy"] == "neural"
        ]
        metrics = ("fitness", "reward", "success", "episode_length")
        by_metric = {
            metric: dict(_mean_by_seed(neural_rows, metric))
            for metric in metrics
        }
        for seed in args.seeds:
            summary_rows.append(
                {
                    "learning_rate": rate,
                    "seed": seed,
                    **{
                        metric: by_metric[metric][seed]
                        for metric in metrics
                    },
                }
            )

    _write_summary(output / "sensitivity_summary.csv", summary_rows)
    _plot_summary(output / "sensitivity_comparison.png", summary_rows)
    (output / "sensitivity_metadata.txt").write_text(
        f"learning_rates={args.learning_rates}\n"
        f"seeds={args.seeds}\n"
        f"epochs={args.epochs}\n"
        f"episodes_per_epoch={args.episodes}\n"
        f"steps_per_episode={args.steps_per_episode}\n"
        f"evaluation_episodes={args.evaluation_episodes}\n"
        f"gamma={args.gamma}\n",
        encoding="utf-8",
    )
    print(f"\n[FINALIZADO] Resultados guardados en {output.resolve()}")


if __name__ == "__main__":
    main()
