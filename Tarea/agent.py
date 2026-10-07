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
        self.limite_tiempo_seguro = max(
            0.0,
            time_limit - max(0.001, time_limit * 0.02),
        )
        self.plan = []
        self.nodos_expandidos = 0 # Medida de esfuerzo requerida
        self.tiempo_inicio = time.perf_counter()
        self.tiempo_transcurrido = 0.0

    def get_action(self, state, valid_actions):
        """Devuelve la siguiente acción (fila, columna) a ejecutar."""
        if self.plan:
            return self.plan.pop(0)

        if self._tiempo_agotado():
            return None

        self.plan = self._realizar_busqueda(state)

        if self.plan:
            return self.plan.pop(0)
        
        return None

    #En general,
    def _realizar_busqueda(self, estado_inicial):
        """Contiene la lógica central del algoritmo de búsqueda A*."""
        # Estados que se van a explorar
        cola = []
        contador = 0 

        # cantidad de fichas que faltan por consumir
        h_inicial = estado_inicial["m"] - estado_inicial["next_piece_index"]
        # cantidad de celdas ocupadas en el estado inicial
        g_inicial = self._contar_ocupadas(estado_inicial["board"])
        # suma de g(n) y h(n) para el estado inicial
        f_inicial = g_inicial + h_inicial

        heapq.heappush(cola, (f_inicial, -estado_inicial["next_piece_index"], contador, estado_inicial, []))

        #json
        visitados = set()
        mejor_plan_parcial = []
        max_profundidad = -1

        while cola:
            #Validacion si se ha superado el tiempo limite de busqueda del agente
            if time.perf_counter() - self.tiempo_inicio >= self.limite_tiempo_seguro:
                  break

            # se extrae la informacion del nodo con el menor valor de f(n) de la cola de prioridad
            f, neg_profundidad, _, estado_actual, camino = heapq.heappop(cola)
            profundidad = -neg_profundidad
            # se suma 1 al contador de nodos expandidos para medir el esfuerzo requerido
            self.nodos_expandidos += 1

            # Si se ha alcanzado una nueva profundidad máxima, se actualiza el mejor plan parcial.
            if profundidad > max_profundidad:
                max_profundidad = profundidad
                mejor_plan_parcial = camino

            # Si se ha alcanzado la profundidad máxima (es decir, se han consumido todas las fichas), se devuelve el camino encontrado.
            if profundidad >= estado_inicial["m"]:
                self.tiempo_transcurrido = time.perf_counter() - self.tiempo_inicio
                return camino

            #Convierte el estado actual en un hash para poder guardarlo en el set de visitados y evitar ciclos.
            estado_hash = self._hash_estado(estado_actual)
            #Agrega el estado actual al conjunto de visitados para evitar ciclos.
            if estado_hash in visitados:
                continue
            visitados.add(estado_hash)

            #Solicita al motor de juego las acciones válidas para el estado actual.
            acciones_validas = self.engine.get_valid_actions(estado_actual)


            # Se recorre cada posible acción y genera un nuevo estado a partir del estado actual y la acción. 
            # Si el nuevo estado es válido, se calcula su función de evaluación f(n) y se agrega a la cola de prioridad para su posterior exploración.
            for accion in acciones_validas:
                try:
                    # se genera un nuevo estado a partir del estado actual y la acción.
                    # y se actualiza el estado del juego con la acción seleccionada.
                    nuevo_estado = self.engine.update_state(estado_actual, accion)

                    # se genera su peso y se calcula su función de evaluación f(n) = g(n) + h(n)
                    # se le da prioridad a g(n) porque entre menos piezas se hayan colocado, más cerca está de la solución.
                    g_nuevo = self._contar_ocupadas(nuevo_estado["board"])
                    h_nuevo = nuevo_estado["m"] - nuevo_estado["next_piece_index"]
                    f_nuevo = g_nuevo + h_nuevo

                    # se crea el camino a partir del camino actual y la acción seleccionada, y se agrega a la cola de prioridad para su posterior exploración.
                    nuevo_camino = camino + [accion]
                    contador += 1

                    heapq.heappush(cola, (f_nuevo, -nuevo_estado["next_piece_index"], contador, nuevo_estado, nuevo_camino))

                except ValueError:
                    continue

        self.tiempo_transcurrido = time.perf_counter() - self.tiempo_inicio
        return mejor_plan_parcial

    def _tiempo_agotado(self):
        """Determina si se alcanzó el límite global de tiempo del agente."""
        return time.perf_counter() - self.tiempo_inicio >= self.limite_tiempo_seguro

    def _contar_ocupadas(self, board):
        """Calcula g(n): la cantidad actual de celdas ocupadas."""
        #recorre la matriz y cuente las celdas que no son None, sumando 1 por cada celda ocupada. Devuelve el total de celdas ocupadas.
        return sum(1 for fila in board for celda in fila if celda is not None)

    def _hash_estado(self, estado):
        """Convierte la matriz en una estructura inmutable para guardarla en el set de visitados."""
        board_tuple = tuple(tuple(celda for celda in fila) for fila in estado["board"])
        return (estado["next_piece_index"], board_tuple)