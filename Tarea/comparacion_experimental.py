"""
comparacion_experimental.py
Comparación experimental de los agentes de TileUp.

Responsabilidad:
- Generar seis configuraciones de instancias.
- Ejecutar ambos agentes con tres semillas.
- Validar las soluciones generadas.
- Guardar las soluciones y las métricas en un CSV.
"""

import argparse
import csv
import statistics
import subprocess
import sys
from pathlib import Path
from generador import InstanceGenerator

class ExperimentalComparison:
    """Ejecuta la comparación de los agentes sobre las mismas instancias."""

    def __init__(self, time_limit, output_directory):
        # Configuraciones distintas de N, K y M para la comparación.
        self.configurations = [(3, 2, 6), (3, 3, 8), (4, 2, 8), (4, 3, 10), (5, 3, 10), (5, 4, 12)]

        # Semillas usadas para repetir cada configuración.
        self.seeds = [1, 2, 3]
        self.time_limit = time_limit
        self.base_path = Path(__file__).resolve().parent
        self.output_directory = self.base_path / output_directory
        self.python = sys.executable

    def run_command(self, command):
        # Ejecutar un script y convertir los errores en mensajes legibles.
        try:
            result = subprocess.run(command, cwd=self.base_path, capture_output=True, text=True, check=False)
        except OSError as error:
            raise ValueError(f"No se pudo ejecutar el comando: {command}") from error

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip()
            raise ValueError(error or "El comando terminó con error.")

        return result.stdout

    def generate_instances(self):
        # Generar seis instancias reproducibles y devolver sus rutas y parámetros.
        instances = []
        for instance_number, (n, k, m) in enumerate(self.configurations, start=1):
            instance_path = self.output_directory / f"instancia_{instance_number}.txt"
            instance_seed = 100 + instance_number

            # Generar la instancia usando el generador de instancias importado.
            generator = InstanceGenerator(n, k, m, instance_seed)
            generator.write_instance(str(instance_path))

            instances.append((instance_number, instance_path, n, k, m))

        return instances

    def validate_solution(self, instance_path, solution_path):
        # Comprobar que el validador independiente acepta la solución.
        output = self.run_command([self.python, "validador.py", str(instance_path), str(solution_path)])
        if "resultado=VALIDO" not in output.splitlines():
            raise ValueError(f"Solución inválida: {solution_path}")

    def parse_metrics(self, output):
        # Convertir las métricas de main.py en datos para el CSV.
        metrics = {}

        # Extraer métricas de la salida del agente.
        for line in output.splitlines():
            if "=" not in line:
                continue
            name, value = line.split("=", 1)
            metrics[name.strip()] = value.strip()

        # Validar que todas las métricas requeridas estén presentes.
        required_metrics = ("colocadas", "ocupadas", "tiempo", "esfuerzo")
        missing_metrics = [name for name in required_metrics if name not in metrics]
        if missing_metrics:
            raise ValueError(
                "Faltan métricas en la ejecución: " + ", ".join(missing_metrics)
            )

        return metrics

    def execute_agent(self, instance_number, instance_path, agent, seed):
        # Ejecutar un agente y guardar su solución con un nombre identificable.
        solution_path = self.output_directory / (
            f"solucion_{instance_number}_{agent}_{seed}.txt"
        )

        output = self.run_command(
            [
                self.python,
                "main.py",
                str(instance_path),
                "--agent",
                agent,
                "--seed",
                str(seed),
                "--time-limit",
                str(self.time_limit),
                "--output",
                str(solution_path),
            ]
        )

        self.validate_solution(instance_path, solution_path)
        return solution_path, self.parse_metrics(output)

    def run(self):
        # Generar instancias y ejecutar los dos agentes con las tres semillas.
        rows = []
        instances = self.generate_instances()

        for instance_number, instance_path, n, k, m in instances:
            for agent in ("search", "evolution"):
                for seed in self.seeds:
                    _, metrics = self.execute_agent(instance_number, instance_path, agent, seed,)
                    rows.append({"Agente": agent,
                            "Instancia": instance_number,
                            "N": n,
                            "K": k,
                            "M": m,
                            "Semilla": seed,
                            "Colocadas": metrics["colocadas"],
                            "Ocupadas": metrics["ocupadas"],
                            "Tiempo": metrics["tiempo"],
                            "Esfuerzo": metrics["esfuerzo"]})

        return rows

    def write_results(self, rows):
        # Escribir las métricas de las 36 ejecuciones en el CSV.
        output_path = self.output_directory / "resultados.csv"
        columns = ["Agente", "Instancia", "N", "K", "M", "Semilla", "Colocadas", "Ocupadas", "Tiempo", "Esfuerzo"]

        try:
            # Guardar los resultados en un archivo CSV con codificación UTF-8.
            with output_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        except OSError as error:
            raise ValueError(
                f"No se pudo escribir el archivo de resultados: {output_path}"
            ) from error

        return output_path

    def write_summary_results(self, rows):
        # Agrupar las ejecuciones por instancia y agente para resumir las semillas.
        groups = {}

        # Agrupar las ejecuciones por instancia y agente para resumir las semillas.
        for row in rows:
            key = (row["Instancia"], row["Agente"])
            groups.setdefault(key, []).append(row)
            #print(f"Grupo {key}: {len(groups[key])} ejecuciones, métricas: {row}")

        # Calcular la media y desviación estándar de cada métrica para cada grupo.
        summary_rows = []
        metrics = ("Colocadas", "Ocupadas", "Tiempo", "Esfuerzo")
        for (instance_number, agent), group in sorted(groups.items()):
            summary = {
                "Instancia": instance_number,
                "N": group[0]["N"],
                "K": group[0]["K"],
                "M": group[0]["M"],
                "Agente": agent,
            }

            # Calcular la media y desviación estándar de cada métrica para cada grupo de intancias
            for metric in metrics:
                values = [float(row[metric]) for row in group]
                summary[f"{metric}_Media"] = statistics.fmean(values)
                summary[f"{metric}_Desviacion"] = (
                    statistics.stdev(values) if len(values) > 1 else 0.0
                )
                if metric == "Tiempo":
                    summary[f"{metric}_Desviacion"] = f"{summary[f'{metric}_Desviacion']:.9f}"
            summary_rows.append(summary)

        output_path = self.output_directory / "resumen.csv"
        columns = ["Instancia", "N", "K", "M", "Agente"]
        for metric in metrics:
            columns.extend((f"{metric}_Media", f"{metric}_Desviacion"))

        try:
            # Guardar el resumen estadístico en la misma carpeta de resultados.
            with output_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerows(summary_rows)
        except OSError as error:
            raise ValueError(
                f"No se pudo escribir el archivo resumen: {output_path}"
            ) from error

        return output_path


def parse_arguments():
    # Configurar el límite de tiempo y la carpeta de salida.
    parser = argparse.ArgumentParser(description="Ejecuta la comparación experimental de TileUp.")
    
    parser.add_argument("--time-limit", type=float, default=0.2, help="Límite de tiempo para cada agente.")
    parser.add_argument("--output-directory", default="comparacion_experimental", 
        help="Carpeta donde se guardarán instancias, soluciones y resultados.")
    return parser.parse_args()


def main():
    # Iniciar la comparación y controlar errores de configuración o ejecución.
    args = parse_arguments()

    try:
        if args.time_limit <= 0:
            raise ValueError("El límite de tiempo debe ser mayor que cero.")

        # Crear la carpeta de salida si no existe y ejecutar la comparación.
        comparison = ExperimentalComparison(
            args.time_limit,
            args.output_directory,
        )
        comparison.output_directory.mkdir(parents=True, exist_ok=True)
        rows = comparison.run()
        output_path = comparison.write_results(rows)
        summary_path = comparison.write_summary_results(rows)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Ejecuciones completadas: {len(rows)}")
    print(f"Resultados guardados en: {output_path}")
    print(f"Resumen guardado en: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
