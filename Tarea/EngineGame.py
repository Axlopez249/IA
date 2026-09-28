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
            action = self.agent.get_action(state, self.get_valid_actions())
            
            if action is None:
                # Si el agente no encuentra movimientos o falla, detenemos el juego
                break
                
            row, col = action
            
            # Verificación de seguridad para evitar que el agente haga un movimiento ilegal
            if not self.is_valid_position(row, col):
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

    def get_next_piece(self) -> Optional[tuple[int, int]]:
        # Devuelve la siguiente ficha pendiente de la secuencia.
        if self.next_piece_index >= self.m:
            return None
        return self.pieces[self.next_piece_index]

    # ------------------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------------------

    def get_state(self):
        # Devuelve una representación del estado actual.
        # Se clona la matriz del tablero para evitar que el agente modifique el real por accidente.
        board_copy = [[cell for cell in row] for row in self.board]
        return {
            'board': board_copy,
            'next_piece_index': self.next_piece_index,
            'pieces': self.pieces,
            'n': self.n,
            'k': self.k,
            'm': self.m
        }

    # ------------------------------------------------------------------
    # ACCIONES / COLOCACIÓN
    # ------------------------------------------------------------------

    def get_valid_actions(self):
        # Devuelve las posiciones vacías donde puede colocarse
        acciones = []
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] is None:
                    acciones.append((r, c))
        return acciones

    def is_valid_position(self, row, col):
        # Determina si una posición está dentro del tablero
        if 0 <= row < self.n and 0 <= col < self.n:
            return self.board[row][col] is None
        return False

    def apply_action(self, state, action):
        # Aplica una acción sobre una representación de estado.
        #
        # Esta función es especialmente útil para que el agente
        # pueda SIMULAR acciones durante la búsqueda sin modificar
        # el tablero real de la partida.
        pass

    def place_piece(self, row, col, piece):
        # Coloca físicamente la ficha elegida en el tablero real.
        self.board[row][col] = piece

    def update_board(self, row, col, piece):
        # Ejecuta la actualización completa del tablero después de colocar una ficha:
        self.place_piece(row, col, piece)
        component = self.get_connected_component(row, col)

        if len(component) >= 2:
            self.apply_fusion(component, (row, col))

    # ------------------------------------------------------------------
    # FUSIÓN
    # ------------------------------------------------------------------

    def get_connected_component(self, row, col):
        # Búsqueda en Profundidad (DFS) para encontrar vecinos del mismo color
        color_colocado = self.board[row][col][0]
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
                if 0 <= nr < self.n and 0 <= nc < self.n:
                    if (nr, nc) not in visitados and self.board[nr][nc] is not None:
                        color_vecino = self.board[nr][nc][0]
                        if color_vecino == color_colocado:
                            visitados.add((nr, nc))
                            pila.append((nr, nc))
                            
        return componente
    
    def apply_fusion(self, component, position):
        row, col = position
        color = self.board[row][col][0]
        
        # Sumar los valores de todas las fichas en la componente conexa[cite: 1]
        suma_total = sum(self.board[r][c][1] for r, c in component)
        
        # Retirar todas las fichas del tablero[cite: 1]
        for r, c in component:
            self.board[r][c] = None
            
        # Dejar una única ficha en la celda original con la suma[cite: 1]
        self.board[row][col] = (color, suma_total)

    # ------------------------------------------------------------------
    # CONDICIONES DE TERMINACIÓN
    # ------------------------------------------------------------------

    def is_victory(self):
        # Determina si se consumieron todas las fichas de la secuencia.
        return self.next_piece_index >= self.m

    def is_defeat(self):
        # Determina si quedan fichas pendientes y no existe ninguna celda vacía donde colocar la siguiente.
        quedan_fichas = self.next_piece_index < self.m
        hay_espacio = len(self.get_valid_actions()) > 0
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
