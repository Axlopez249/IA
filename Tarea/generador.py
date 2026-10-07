"""
generador.py
Generador de instancias reproducibles de TileUp.

Responsabilidad:
- Recibir N, K y M.
- Generar una secuencia reproducible de fichas.
- Escribir la instancia en el formato del parser actual.
"""

import argparse
import random
import sys


class InstanceGenerator:
    """Genera una instancia de TileUp usando una semilla fija."""

    def __init__(self, n, k, m, seed):
        # Guardar los parámetros de la instancia y crear el generador aleatorio.
        self.n = n
        self.k = k
        self.m = m
        self.seed = seed
        self.random = random.Random(seed)

    def generate_pieces(self):
        # Generar M fichas con color entre 1 y K y valor positivo.
        pieces = []
        for _ in range(self.m):
            color = self.random.randint(1, self.k)
            value = self.random.randint(1, 10)
            pieces.append((color, value))
        return pieces

    def write_instance(self, output_path):
        # Escribir la instancia respetando el formato que consume el motor.
        pieces = self.generate_pieces()

        try:
            with open(output_path, "w") as file:
                file.write("# TileUp\n")
                file.write(f"{self.n} {self.k}\n")
                file.write(f"{self.m}\n")

                for color, value in pieces:
                    file.write(f"{color} {value}\n")
        except OSError as error:
            raise ValueError(
                f"No se pudo escribir el archivo de salida: {output_path}"
            ) from error


def parse_arguments():
    # Configurar los argumentos de la línea de comandos.
    parser = argparse.ArgumentParser(
        description="Genera una instancia reproducible de TileUp."
    )
    parser.add_argument("N", type=int, help="Tamaño del tablero.")
    parser.add_argument("K", type=int, help="Cantidad de colores.")
    parser.add_argument("M", type=int, help="Cantidad de fichas.")
    parser.add_argument(
        "-s",
        "-semilla",
        "--semilla",
        "-seed",
        "--seed",
        dest="seed",
        type=int,
        required=True,
        help="Semilla aleatoria.",
    )
    parser.add_argument(
        "-o",
        "-salida",
        "--salida",
        "-output",
        "--output",
        dest="output",
        default="instancia.txt",
        help="Ruta del archivo de salida.",
    )
    return parser.parse_args()


def main():
    # Iniciar el generador y controlar los errores de entrada y salida.
    args = parse_arguments()

    try:
        if args.N <= 0:
            raise ValueError("N debe ser mayor que cero.")
        if args.K <= 0:
            raise ValueError("K debe ser mayor que cero.")
        if args.M <= 0:
            raise ValueError("M debe ser mayor que cero.")

        generator = InstanceGenerator(args.N, args.K, args.M, args.seed)
        generator.write_instance(args.output)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Instancia generada: {args.output}")
    print(f"N={args.N} K={args.K} M={args.M} semilla={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
