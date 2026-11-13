"""Genera curvas de aprendizaje con media y desviacion entre semillas.

Este modulo no entrena redes ni modifica checkpoints. Lee las metricas que
cada ejecucion guardo durante el entrenamiento y las transforma en una figura
para analizar la variabilidad del aprendizaje entre semillas.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_results(
    results_dir: Path,
    species: str,
    metric: str,
) -> list[list[float]]:
    # Cada archivo representa una ejecucion independiente del entrenamiento.
    # La carpeta esperada es results_dir/seed-N/training_results.json.
    curves: list[list[float]] = []
    for path in sorted(results_dir.glob("seed-*/training_results.json")):
        # Se carga el JSON completo para conservar el mismo formato producido
        # por train_policies.py y seleccionar solo la especie y metrica pedidas.
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload.get("species", {}).get(species, {}).get(metric, [])
        if isinstance(values, list) and values:
            # Convertir a float permite calcular medias aunque el JSON contenga
            # enteros, por ejemplo, en la serie de exitos.
            curves.append([float(value) for value in values])
    return curves


def _statistics(curves: list[list[float]]) -> tuple[list[float], list[float]]:
    # La longitud de las curvas puede variar si un episodio termina antes.
    # Por eso cada episodio se calcula usando solo las semillas que tienen
    # un valor disponible en esa posicion.
    import statistics

    size = max(len(curve) for curve in curves)
    means: list[float] = []
    spreads: list[float] = []
    for index in range(size):
        # Reune el resultado del mismo episodio en todas las semillas.
        values = [
            curve[index]
            for curve in curves
            if index < len(curve)
        ]
        # La media representa el comportamiento promedio y la desviacion
        # muestra cuanto cambia el resultado entre ejecuciones independientes.
        means.append(statistics.mean(values))
        spreads.append(statistics.stdev(values) if len(values) > 1 else 0.0)
    return means, spreads


def main() -> None:
    # Los argumentos permiten reutilizar el script con diferentes carpetas
    # de checkpoints y separar los graficos de los datos de entrenamiento.
    parser = argparse.ArgumentParser(
        description="Genera curvas de recompensa con media y desviacion."
    )
    parser.add_argument("--results", default="checkpoints")
    parser.add_argument("--output", default="results")
    args = parser.parse_args()

    # matplotlib se importa aqui para que el resto del proyecto pueda usar
    # entrenamiento y evaluacion sin cargar una dependencia grafica.
    import matplotlib.pyplot as plt

    results_dir = Path(args.results)
    output_dir = Path(args.output)
    # La carpeta de salida se crea si todavia no existe.
    output_dir.mkdir(parents=True, exist_ok=True)

    # Se crea una cuadricula de tres metricas por dos especies:
    # recompensa, longitud del episodio y exito.
    figure, axes = plt.subplots(3, 2, figsize=(12, 13), sharex="col")
    metrics = (
        ("rewards", "Recompensa acumulada"),
        ("episode_lengths", "Longitud del episodio"),
        ("successes", "Exito (1=sobrevive, 0=muere)"),
    )
    for species in ("herbivore", "carnivore"):
        # La primera columna corresponde a herbivoros y la segunda
        # a carnivoros.
        column = 0 if species == "herbivore" else 1
        for row, (metric, label) in enumerate(metrics):
            curves = _load_results(results_dir, species, metric)
            if not curves:
                # Un grafico sin datos seria engañoso, por lo que se informa
                # explicitamente que falta el resultado de entrenamiento.
                raise FileNotFoundError(
                    f"No hay datos de {metric} para {species} en {results_dir}."
                )
            means, spreads = _statistics(curves)
            episodes = list(range(1, len(means) + 1))
            # La banda sombreada representa media +/- desviacion estandar.
            lower = [mean - spread for mean, spread in zip(means, spreads)]
            upper = [mean + spread for mean, spread in zip(means, spreads)]
            axis = axes[row][column]
            axis.plot(episodes, means, label="media")
            axis.fill_between(
                episodes,
                lower,
                upper,
                alpha=0.2,
                label="desviacion",
            )
            # Se etiquetan los ejes para que cada grafico pueda interpretarse
            # sin consultar el codigo ni los archivos JSON.
            axis.set_title(f"{species}: {label}")
            axis.set_xlabel("Episodio")
            axis.set_ylabel(label)
            axis.legend()
            axis.grid(alpha=0.3)

    # Se agrega un titulo general y se ajustan los espacios para evitar que
    # las etiquetas de los subgraficos se superpongan.
    figure.suptitle("Curvas de aprendizaje REINFORCE")
    figure.tight_layout()
    # La figura queda disponible para incluirla directamente en el informe.
    figure.savefig(output_dir / "learning_curves.png", dpi=150)
    print(f"Grafico guardado en {output_dir / 'learning_curves.png'}")


if __name__ == "__main__":
    main()
