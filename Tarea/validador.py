"""
validador.py
Validador independiente de soluciones de TileUp.

Responsabilidad:
- Leer la instancia y la solución.
- Comprobar que cada movimiento sea legal.
- Reproducir las colocaciones y las fusiones.
- Mostrar las métricas finales de la solución.
"""

import argparse
import sys


class SolutionValidator:
    """Valida una solución reproduciendo la partida desde cero. """

    def __init__(self, instance_path):
        # Cargar la instancia y preparar el tablero vacío.
        self.n, self.k, self.pieces = self.load_instance(instance_path)
        self.m = len(self.pieces)
        self.board = [[None for _ in range(self.n)] for _ in range(self.n)]
        self.moves = 0

    def load_instance(self, instance_path):
        # Leer la instancia respetando el formato del motor principal.
        try:
            with open(instance_path, "r") as file:
                lines = file.readlines()
        except OSError as error:
            raise ValueError(
                f"No se pudo abrir el archivo de instancia: {instance_path}"
            ) from error

        useful_lines = []
        # Ignorar líneas vacías y comentarios, pero conservar el número de línea para reportar errores.
        for line_number, line in enumerate(lines, start=1):
            line = line.split("#", 1)[0].strip()
            if line:
                useful_lines.append((line_number, line))


        # Validar que la instancia tenga al menos tres líneas útiles (N K y M).
        if len(useful_lines) < 3:
            raise ValueError("La instancia no contiene todos los datos necesarios.")

        # Validar la primera línea: N y K.
        line_number, line = useful_lines[0]
        values = line.split()
        if len(values) != 2:
            raise ValueError(
                f"Línea {line_number}: se esperaban N y K."
            )

        # Validar que N y K sean enteros positivos.
        try:
            n, k = map(int, values)
        except ValueError as error:
            raise ValueError(
                f"Línea {line_number}: N y K deben ser enteros."
            ) from error

        if n <= 0 or k <= 0:
            raise ValueError(
                f"Línea {line_number}: N y K deben ser mayores que cero."
            )

        # Validar la segunda línea: M.
        line_number, line = useful_lines[1]
        values = line.split()
        if len(values) != 1:
            raise ValueError(f"Línea {line_number}: M debe ser un único entero.")

        # Validar que M sea un entero positivo.
        try:
            m = int(values[0])
        except ValueError as error:
            raise ValueError(
                f"Línea {line_number}: M debe ser un entero."
            ) from error

        # Validar que M sea mayor que cero.
        if m <= 0:
            raise ValueError(
                f"Línea {line_number}: M debe ser mayor que cero."
            )

        # Validar que la cantidad de fichas declaradas coincida con M.
        piece_lines = useful_lines[2:]
        if len(piece_lines) != m:
            raise ValueError(
                f"Se declararon {m} fichas, pero se encontraron {len(piece_lines)}."
            )

        # Validar las líneas de las fichas. 
        pieces = []
        for line_number, line in piece_lines:
            values = line.split()
            if len(values) != 2:
                raise ValueError(
                    f"Línea {line_number}: la ficha debe tener color y valor."
                )

            # Validar que el color y el valor sean enteros y estén dentro de los rangos permitidos.
            try:
                color, value = map(int, values)
            except ValueError as error:
                raise ValueError(
                    f"Línea {line_number}: el color y el valor deben ser enteros."
                ) from error

            if not 1 <= color <= k:
                raise ValueError(
                    f"Línea {line_number}: el color debe estar entre 1 y {k}."
                )
            if value < 1:
                raise ValueError(
                    f"Línea {line_number}: el valor debe ser mayor o igual que 1."
                )

            pieces.append((color, value))

        return n, k, pieces

    def read_solution(self, solution_path):
        # Leer movimientos; las líneas de comentario se ignoran.
        try:
            with open(solution_path, "r") as file:
                lines = file.readlines()
        except OSError as error:
            raise ValueError(
                f"No se pudo abrir el archivo de solución: {solution_path}"
            ) from error

        # Validar cada línea de la solución y convertirla en una lista de movimientos.
        moves = []
        for line_number, line in enumerate(lines, start=1):
            line = line.split("#", 1)[0].strip()
            if not line:
                continue

            # Validar que cada línea tenga exactamente tres valores: índice de ficha, fila y columna.
            values = line.split()
            if len(values) != 3:
                raise ValueError(
                    f"Línea {line_number}: el movimiento debe tener índice, fila y columna."
                )

            # Validar que el índice de ficha, la fila y la columna sean enteros.
            try:
                piece_index, row, col = map(int, values)
            except ValueError as error:
                raise ValueError(
                    f"Línea {line_number}: índice, fila y columna deben ser enteros."
                ) from error

            moves.append((piece_index, row, col, line_number))

        return moves

    def validate(self, solution_path):
        # Reproducir cada movimiento en el tablero independiente del motor.
        moves = self.read_solution(solution_path)

        # Validar que los movimientos estén en orden y sean legales.
        for expected_index, (piece_index, row, col, line_number) in enumerate(moves):
            
            # Validar que el índice de ficha sea el esperado y que esté dentro del rango permitido.
            if piece_index != expected_index:
                raise ValueError(
                    f"Línea {line_number}: se esperaba el índice {expected_index}, "
                    f"pero se encontró {piece_index}."
                )

            # Validar que el índice de ficha esté dentro del rango permitido.
            if piece_index < 0 or piece_index >= self.m:
                raise ValueError(
                    f"Línea {line_number}: el índice de ficha está fuera de rango."
                )

            # Validar que la fila y la columna estén dentro del tablero.
            if not (0 <= row < self.n and 0 <= col < self.n):
                raise ValueError(
                    f"Línea {line_number}: la celda ({row}, {col}) está fuera del tablero."
                )

            # Validar que la celda esté vacía antes de colocar la ficha.
            if self.board[row][col] is not None:
                raise ValueError(
                    f"Línea {line_number}: la celda ({row}, {col}) ya está ocupada."
                )

            # Colocar la ficha y aplicar la fusión de componentes del mismo color.
            self.board[row][col] = self.pieces[piece_index]
            component = self.get_connected_component(row, col)
            if len(component) >= 2:
                self.apply_fusion(component, row, col)

            self.moves += 1

        return self.get_metrics()

    def get_connected_component(self, row, col):
        # Buscar las fichas del mismo color conectadas ortogonalmente.
        color = self.board[row][col][0]
        component = []
        visited = {(row, col)}
        pending = [(row, col)]

        #Búsqueda en profundidad para encontrar todas las fichas conectadas del mismo color.
        while pending:
            current_row, current_col = pending.pop()
            component.append((current_row, current_col))

            #Explorar las cuatro direcciones ortogonales (arriba, abajo, izquierda, derecha).
            for delta_row, delta_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_row = current_row + delta_row
                next_col = current_col + delta_col

                # Validar que la celda esté dentro del tablero, no haya sido visitada y tenga el mismo color.
                if not (0 <= next_row < self.n and 0 <= next_col < self.n):
                    continue
                if (next_row, next_col) in visited:
                    continue
                if self.board[next_row][next_col] is not None:
                    if self.board[next_row][next_col][0] == color:
                        visited.add((next_row, next_col))
                        pending.append((next_row, next_col))

        return component

    def apply_fusion(self, component, row, col):
        # Sumar la componente y conservar el resultado en la celda colocada.
        color = self.board[row][col][0]
        total_value = sum(self.board[r][c][1] for r, c in component)

        # Vaciar las celdas de la componente fusionada, excepto la celda donde se colocó la ficha.
        for component_row, component_col in component:
            self.board[component_row][component_col] = None

        self.board[row][col] = (color, total_value)

    def get_metrics(self):
        # Calcular las métricas finales del tablero reproducido.
        occupied = sum(
            1
            for row in self.board
            for cell in row
            if cell is not None
        )
        maximum = max(
            (cell[1] for row in self.board for cell in row if cell is not None),
            default=0,
        )
        return {
            "colocadas": self.moves,
            "ocupadas": occupied,
            "mayor": maximum,
        }


def parse_arguments():
    # Configurar el analizador de argumentos para el validador de soluciones.
    parser = argparse.ArgumentParser(
        description="Valida una solución de TileUp."
    )
    parser.add_argument("instance_path", help="Ruta del archivo de instancia.")
    parser.add_argument("solution_path", help="Ruta del archivo de solución.")
    return parser.parse_args()


def main():
    #funcion para iniciar el validador de soluciones, parsear los argumentos y mostrar las métricas finales.
    args = parse_arguments()

    try:
        # Validar que los archivos de instancia y solución existan.
        validator = SolutionValidator(args.instance_path)
        metrics = validator.validate(args.solution_path)
    except (OSError, ValueError) as error:
        print("resultado=INVALIDO")
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"colocadas={metrics['colocadas']}")
    print(f"ocupadas={metrics['ocupadas']}")
    print(f"mayor={metrics['mayor']}")
    print("resultado=VALIDO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
