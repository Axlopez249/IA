"""Agente de búsqueda para TileUp."""

import heapq
from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
    from EngineGame import GameEngine


class SearchAgent:
    """Agente de búsqueda que utiliza el algoritmo A*."""

    def __init__(self, engine: "GameEngine", seed: int, time_limit: float):
        self.engine = engine
        self.seed = seed
        self.time_limit = time_limit
        self.plan = []
        self.nodos_expandidos = 0 # Medida de esfuerzo requerida

    def get_action(self, state, valid_actions):
        """Devuelve la siguiente acción (fila, columna) a ejecutar."""
        if self.plan:
            return self.plan.pop(0)

        self.plan = self._realizar_busqueda(state)

        if self.plan:
            return self.plan.pop(0)
        
        return None

    def _realizar_busqueda(self, estado_inicial):
        """Contiene la lógica central del algoritmo de búsqueda A*."""
        tiempo_inicio = time.time()
        self.nodos_expandidos = 0
        
        cola = []
        contador = 0 

        h_inicial = estado_inicial["m"] - estado_inicial["next_piece_index"]
        g_inicial = self._contar_ocupadas(estado_inicial["board"])
        f_inicial = g_inicial + h_inicial

        heapq.heappush(cola, (f_inicial, -estado_inicial["next_piece_index"], contador, estado_inicial, []))

        visitados = set()
        mejor_plan_parcial = []
        max_profundidad = -1

        while cola:
            if time.time() - tiempo_inicio >= self.time_limit:
                  break

            f, neg_profundidad, _, estado_actual, camino = heapq.heappop(cola)
            profundidad = -neg_profundidad
            self.nodos_expandidos += 1

            if profundidad > max_profundidad:
                max_profundidad = profundidad
                mejor_plan_parcial = camino

            if profundidad >= estado_inicial["m"]:
                return camino

            estado_hash = self._hash_estado(estado_actual)
            if estado_hash in visitados:
                continue
            visitados.add(estado_hash)

            acciones_validas = self.engine.get_valid_actions(estado_actual)

            for accion in acciones_validas:
                try:
                    nuevo_estado = self.engine.update_state(estado_actual, accion)
                    
                    g_nuevo = self._contar_ocupadas(nuevo_estado["board"])
                    h_nuevo = nuevo_estado["m"] - nuevo_estado["next_piece_index"]
                    f_nuevo = g_nuevo + h_nuevo

                    nuevo_camino = camino + [accion]
                    contador += 1

                    heapq.heappush(cola, (f_nuevo, -nuevo_estado["next_piece_index"], contador, nuevo_estado, nuevo_camino))

                except ValueError:
                    continue

        return mejor_plan_parcial

    def _contar_ocupadas(self, board):
        """Calcula g(n): la cantidad actual de celdas ocupadas."""
        return sum(1 for fila in board for celda in fila if celda is not None)

    def _hash_estado(self, estado):
        """Convierte la matriz en una estructura inmutable para guardarla en el set de visitados."""
        board_tuple = tuple(tuple(celda for celda in fila) for fila in estado["board"])
        return (estado["next_piece_index"], board_tuple)