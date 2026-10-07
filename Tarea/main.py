"""Punto de entrada por línea de comandos para TileUp."""

import argparse
import os
import random
import sys
import time

from EngineGame import GameEngine


def build_agent(engine: GameEngine, agent_name: str, seed: int, time_limit: float):
    """Crea el agente seleccionado por la línea de comandos.

    Los módulos concretos se incorporarán cuando se implementen los agentes.
    """
    try:
        if agent_name == "search":
            from agent import SearchAgent

            return SearchAgent(
                engine=engine,
                seed=seed,
                time_limit=time_limit,
            )

        if agent_name == "evolution":
            from evolutionary_agent import EvolutionaryAgent

            return EvolutionaryAgent(
                engine=engine,
                seed=seed,
                time_limit=time_limit,
            )
    except ModuleNotFoundError as error:
        raise ValueError(
            f"No se encontró el módulo del agente '{agent_name}'. "
            "Todavía falta implementarlo."
        ) from error
    except TypeError as error:
        raise ValueError(
            f"La interfaz del agente '{agent_name}' todavía no acepta "
            "seed y time_limit."
        ) from error

    raise ValueError(f"Agente desconocido: {agent_name}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Ejecuta una partida de TileUp.")
    parser.add_argument("instance_path", help="Ruta del archivo de instancia.")
    parser.add_argument(
        "--agent",
        choices=("search", "evolution"),
        required=True,
        help="Agente que se utilizará.",
    )
    parser.add_argument("--seed", type=int, required=True, help="Semilla aleatoria.")
    parser.add_argument(
        "--time-limit",
        type=float,
        required=True,
        help="Límite de tiempo en segundos.",
    )
    parser.add_argument(
        "--output",
        default="solution.txt",
        help="Ruta del archivo de solución.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    random.seed(args.seed)

    try:
        if args.time_limit <= 0:
            raise ValueError("El límite de tiempo debe ser mayor que cero.")

        if not os.path.isfile(args.instance_path):
            raise ValueError(
                f"El archivo de instancia no existe: {args.instance_path}"
            )

        engine = GameEngine(args.instance_path)
        agent = build_agent(engine, args.agent, args.seed, args.time_limit)
        engine.agent = agent
        tiempo_inicio = time.perf_counter()
        engine.run()
        tiempo_transcurrido = time.perf_counter() - tiempo_inicio
        engine.write_solution(args.output)

        if hasattr(engine.agent, "nodos_expandidos"):
            esfuerzo = engine.agent.nodos_expandidos
        else:
            esfuerzo = engine.agent.evaluaciones_aptitud

        print(f"colocadas={len(engine.solution)}")
        print(f"ocupadas={engine.get_occupied_cells()}")
        print(f"mayor={engine.get_max_piece_value()}")
        print(f"tiempo={tiempo_transcurrido:.6f}")
        print(f"esfuerzo={esfuerzo}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
