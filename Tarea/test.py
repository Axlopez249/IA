from EngineGame import GameEngine

# Creamos un agente falso (dummy) solo para poder iniciar el motor
class DummyAgent:
    pass

def probar_motor():
    # Crear el archivo de prueba de la instancia (basado en el PDF)
    texto_instancia = """# TileUp
4 3
6
1 2
2 1
1 3
3 1
1 1
2 4
"""
    with open("ejemplo.txt", "w") as f:
        f.write(texto_instancia)

    # Inicializar el motor
    print("--- INICIANDO TILEUP ---")
    engine = GameEngine("ejemplo.txt", DummyAgent())
    print(f"Tablero de {engine.n}x{engine.n}, {engine.k} colores, {engine.m} fichas de secuencia.\n")
    engine.show_board()

    # Probar colocar fichas manualmente para ver la física
    
    # Colocar Ficha 0: Color 1, Valor 2
    ficha_0 = engine.get_next_piece()
    print(f"Turno 1: Colocando ficha {ficha_0} en (0, 0)")
    engine.update_board(0, 0, ficha_0)
    engine.next_piece_index += 1
    engine.show_board()

    # Colocar Ficha 1: Color 2, Valor 1
    ficha_1 = engine.get_next_piece()
    print(f"Turno 2: Colocando ficha {ficha_1} en (0, 1) - Diferente color, no pasa nada")
    engine.update_board(0, 1, ficha_1)
    engine.next_piece_index += 1
    engine.show_board()

    # Colocar Ficha 2: Color 1, Valor 3 en (1,0) (Justo debajo de la ficha 0)
    ficha_2 = engine.get_next_piece()
    print(f"Turno 3: Colocando ficha {ficha_2} en (1, 0) - MISMO COLOR QUE ARRIBA, DEBE FUSIONARSE")
    engine.update_board(1, 0, ficha_2)
    engine.next_piece_index += 1
    engine.show_board()

if __name__ == "__main__":
    probar_motor()