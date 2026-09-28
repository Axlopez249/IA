"""
EngineGame.py
Motor principal de TileUp.

Responsabilidad:
- Leer/cargar la instancia.
- Mantener el estado real del tablero.
- Consumir las fichas en el orden de la instancia.
- Consultar al agente para decidir dónde colocar cada ficha.
- Aplicar la colocación y las reglas de fusión.
- Detectar victoria/derrota.
- Generar la solución final.

El motor es independiente del algoritmo de búsqueda:
el agente decide la acción; el motor aplica las reglas del juego.

#Indicacion de la IA ------------------------------------------
Como el profesor indicó que el motor es independiente del algoritmo de búsqueda, 
self.agent.get_action(...) es un método inventado en este código como punto de contacto. 
Cuando tu compañero termine los agentes en agent.py y evolutionary_agent.py, 
olo deben asegurarse de que la función principal de sus agentes se llame get_action 
(o cambiar el nombre aquí en el motor para que coincida) y que reciba el estado para devolver una tupla (fila, columna).
---------------------------------------------------------------


"""

from typing import Any, Optional


class GameEngine:
    """Motor principal que controla la ejecución de una partida de TileUp."""

    def __init__(self, instance_path: str, agent: Any):
        # Carga la instancia y prepara el tablero, la secuencia de fichas
        # y la información necesaria para ejecutar la partida.
        self.agent = agent
        self.n = 0
        self.k = 0
        self.m = 0
        self.board = []
        self.pieces = []
        self.next_piece_index = 0
        self.solution = []

        self.load_instance(instance_path)

    # ------------------------------------------------------------------
    # EJECUCIÓN PRINCIPAL
    # ------------------------------------------------------------------

    def run(self):
        # El ciclo continúa mientras no haya victoria ni derrota
        while not self.is_victory() and not self.is_defeat():
            # Obtener la siguiente ficha de la secuencia (tupla (color, valor))
            piece = self.get_next_piece()
            
            # Construir el estado actual retorna un json con el tablero, la secuencia de fichas y el índice de la siguiente ficha
            state = self.get_state()
            
            # Consultar al agente (asumimos que tendrá un método 'get_action')
            # El motor es independiente, solo le pide coordenadas al agente
            action = self.agent.get_action(state, self.get_valid_actions(state))
            
            if action is None:
                # Si el agente no encuentra movimientos o falla, detenemos el juego
                break
                
            row, col = action
            
            # Verificación de seguridad para evitar que el agente haga un movimiento ilegal
            if not self.is_valid_position(row, col, state):
                raise ValueError(f"El agente intentó un movimiento ilegal en la celda ({row}, {col})")
            
            # Aplicar colocación y reglas de fusión
            self.update_board(row, col, piece)
            
            # Guardar la colocación realizada para el archivo de salida
            self.record_action(self.next_piece_index, row, col)
            
            # Avanzar el turno
            self.next_piece_index += 1

    # ------------------------------------------------------------------
    # INSTANCIA Y SECUENCIA DE FICHAS
    # ------------------------------------------------------------------

    def load_instance(self, instance_path):
        # Leer el archivo de texto respetando el formato
        with open(instance_path, 'r') as f:
            lineas = f.readlines()

        # Filtrar líneas en blanco y comentarios (las que empiezan con #)[cite: 1]
        lineas_limpias = []
        for linea in lineas:
            l = linea.strip()
            if l and not l.startswith('#'):
                lineas_limpias.append(l)

        # Extraer N y K separados por espacio (primera línea útil)[cite: 1]
        self.n, self.k = map(int, lineas_limpias[0].split())
        
        # Extraer M (segunda línea útil)[cite: 1]
        self.m = int(lineas_limpias[1])

        # Extraer la secuencia de fichas (el resto de las líneas)[cite: 1]
        self.pieces = []
        for i in range(2, 2 + self.m):
            color, valor = map(int, lineas_limpias[i].split())
            self.pieces.append((color, valor))

        # Inicializar el tablero vacío de NxN[cite: 1]
        self.board = [[None for _ in range(self.n)] for _ in range(self.n)]
        self.next_piece_index = 0

    def get_next_piece(self, state=None) -> Optional[tuple[int, int]]:
        # Devuelve la siguiente ficha pendiente de la secuencia.
        if state is None:
            next_piece_index = self.next_piece_index
            pieces = self.pieces
            m = self.m
        else:
            next_piece_index = state['next_piece_index']
            pieces = state['pieces']
            m = state['m']

        if next_piece_index >= m:
            return None
        return pieces[next_piece_index]

    # ------------------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------------------

    # Funcion que devuelve una copia independiente del estado real o del estado indicado,
    # para evitar que el agente modifique el estado real por accidente
    def get_state(self, state=None):
        # Devuelve una copia independiente del estado real o del estado indicado.
        # Se clona la matriz del tablero para evitar que el agente modifique el real por accidente.
        source = state
        if source is None:
            source = {
                'board': self.board,
                'next_piece_index': self.next_piece_index,
                'pieces': self.pieces,
                'n': self.n,
                'k': self.k,
                'm': self.m
            }

        board_copy = [[cell for cell in row] for row in source['board']]
        return {
            'board': board_copy,
            'next_piece_index': source['next_piece_index'],
            'pieces': list(source['pieces']),
            'n': source['n'],
            'k': source['k'],
            'm': source['m']
        }

    # ------------------------------------------------------------------
    # ACCIONES / COLOCACIÓN
    # ------------------------------------------------------------------

    # Funcion que devuelve las posiciones vacías donde puede colocarse la siguiente ficha, ya sea en el tablero real o en un estado simulado
    def get_valid_actions(self, state=None):
        # Devuelve las posiciones vacías donde puede colocarse
        board, n = self._board_and_size(state)
        acciones = []
        for r in range(n):
            for c in range(n):
                if board[r][c] is None:
                    acciones.append((r, c))
        return acciones

    # Funcion que determina si una posición es válida para colocar una ficha, ya sea en el tablero real o en un estado simulado
    def is_valid_position(self, row, col, state=None):
        # Determina si una posición está dentro del tablero
        board, n = self._board_and_size(state)
        if 0 <= row < n and 0 <= col < n:
            return board[row][col] is None
        return False

    # Funcion para retornar el tablero y su tamaño, ya sea del estado real o de un estado simulado
    def _board_and_size(self, state=None):
        if state is None:
            return self.board, self.n
        return state['board'], state['n']

    # Funcion para colocar una ficha en el tablero real o en un estado simulado
    def place_piece(self, row, col, piece, state=None):
        # Coloca una ficha en el tablero real o en el estado indicado.
        board, _ = self._board_and_size(state)
        board[row][col] = piece

    # Funcion para actualizar el tablero real o un estado simulado, aplicando la colocación y las reglas de fusión
    def update_board(self, row, col, piece, state=None):
        # Ejecuta la actualización completa del tablero real o simulado.
        self.place_piece(row, col, piece, state)
        component = self.get_connected_component(row, col, state)

        if len(component) >= 2:
            self.apply_fusion(component, (row, col), state)

        return state

    # Funcion que actualiza el estado simulado a partir de una acción, 
    # consumiendo la siguiente ficha y aplicando la colocación y las reglas de fusión
    def update_state(self, state, action):
        # Devuelve un nuevo estado resultante de consumir la siguiente ficha.
        # El estado recibido nunca se modifica, lo que permite crear ramas.
        next_state = self.get_state(state)
        next_piece = self.get_next_piece(next_state)
        if next_piece is None:
            raise ValueError("No quedan fichas para aplicar la acción.")

        try:
            row, col = action
        except (TypeError, ValueError) as error:
            raise ValueError("La acción debe ser una tupla (fila, columna).") from error

        if not self.is_valid_position(row, col, next_state):
            raise ValueError(f"La acción ({row}, {col}) no es válida.")

        self.update_board(row, col, next_piece, next_state)
        next_state['next_piece_index'] += 1
        return next_state

    # Funcion que aplica una acción al estado, alias de update_state para los agentes que ya usan este nombre
    def apply_action(self, state, action):
        # Alias de update_state para los agentes que ya usan este nombre.
        return self.update_state(state, action)

    # ------------------------------------------------------------------
    # FUSIÓN
    # ------------------------------------------------------------------

    # Funcion que devuelve la componente conexa de fichas del mismo color a partir de una posición, ya sea en el tablero real o en un estado simulado
    def get_connected_component(self, row, col, state=None):
        # Búsqueda en Profundidad (DFS) para encontrar vecinos del mismo color
        board, n = self._board_and_size(state)
        color_colocado = board[row][col][0]
        visitados = set()
        componente = []
        pila = [(row, col)]
        visitados.add((row, col))

        while pila:
            r, c = pila.pop()
            componente.append((r, c))
            
            # Revisar vecindad ortogonal: arriba, abajo, izquierda, derecha[cite: 1]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                
                # Si está dentro del tablero y no es vacía
                if 0 <= nr < n and 0 <= nc < n:
                    if (nr, nc) not in visitados and board[nr][nc] is not None:
                        color_vecino = board[nr][nc][0]
                        if color_vecino == color_colocado:
                            visitados.add((nr, nc))
                            pila.append((nr, nc))
                            
        return componente

    # Funcion que aplica la fusión de fichas en el tablero real o en un estado simulado, sumando sus valores y dejando una única ficha
    def apply_fusion(self, component, position, state=None):
        board, _ = self._board_and_size(state)
        row, col = position
        color = board[row][col][0]
        
        # Sumar los valores de todas las fichas en la componente conexa[cite: 1]
        suma_total = sum(board[r][c][1] for r, c in component)
        
        # Retirar todas las fichas del tablero[cite: 1]
        for r, c in component:
            board[r][c] = None
            
        # Dejar una única ficha en la celda original con la suma[cite: 1]
        board[row][col] = (color, suma_total)

    # ------------------------------------------------------------------
    # CONDICIONES DE TERMINACIÓN
    # ------------------------------------------------------------------

    def is_victory(self, state=None):
        # Determina si se consumieron todas las fichas de la secuencia.
        next_piece_index = self.next_piece_index if state is None else state['next_piece_index']
        m = self.m if state is None else state['m']
        return next_piece_index >= m

    def is_defeat(self, state=None):
        # Determina si quedan fichas pendientes y no existe ninguna celda vacía donde colocar la siguiente.
        next_piece_index = self.next_piece_index if state is None else state['next_piece_index']
        m = self.m if state is None else state['m']
        quedan_fichas = next_piece_index < m
        hay_espacio = len(self.get_valid_actions(state)) > 0
        return quedan_fichas and not hay_espacio

    # ------------------------------------------------------------------
    # SOLUCIÓN Y MÉTRICAS
    # ------------------------------------------------------------------

    def record_action(self, piece_index, row, col):
        # Guarda la colocación realizada para posteriormente
        self.solution.append((piece_index, row, col))

    def get_solution(self):
        # Devuelve las colocaciones realizadas en el orden en que se consumieron las fichas.
        return self.solution

    def get_occupied_cells(self):
        # Devuelve la cantidad de celdas ocupadas al finalizar o en el estado actual.
        count = 0
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] is not None:
                    count += 1
        return count

    def get_max_piece_value(self):
        # Encuentra la ficha de mayor valor presente en el tablero
        max_val = 0
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] is not None:
                    valor = self.board[r][c][1]
                    if valor > max_val:
                        max_val = valor
        return max_val

    def write_solution(self, output_path):
        # Escribe el archivo de solución respetando el formato del profesor
        with open(output_path, 'w') as f:
            for move in self.solution:
                # Escribe: índice fila columna separados por espacio
                f.write(f"{move[0]} {move[1]} {move[2]}\n")
            
            # Línea final con el resumen de métricas
            colocadas = len(self.solution)
            ocupadas = self.get_occupied_cells()
            mayor = self.get_max_piece_value()
            f.write(f"# colocadas = {colocadas} ocupadas = {ocupadas} mayor = {mayor}\n")

    # ------------------------------------------------------------------
    # PRESENTACIÓN / DEPURACIÓN
    # ------------------------------------------------------------------

    def show_board(self):
        # Muestra el tablero en la consola de manera legible.
        for row in self.board:
            fila_texto = []
            for cell in row:
                if cell is None:
                    fila_texto.append("[  ]")
                else:
                    color, valor = cell
                    fila_texto.append(f"[{color}:{valor}]")
            print(" | ".join(fila_texto))
        print(f"Fichas colocadas: {self.next_piece_index}/{self.m}\n")
