import os
import sys
import tempfile
import unittest

# Asegurarse de que el directorio raíz del proyecto esté en sys.path para importar EngineGame.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from EngineGame import GameEngine


class TestGameEngine(unittest.TestCase):
    def _write_instance(self, content):
        # Crear un archivo temporal para la instancia de prueba.
        temp_dir = tempfile.mkdtemp(prefix="tileup_tests_")
        path = os.path.join(temp_dir, "instancia.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_carga_instancia_valida(self):
        # Crear una instancia válida y verificar que se cargue correctamente.
        path = self._write_instance("""# TileUp
                                    4 3
                                    6
                                    1 2
                                    2 1
                                    1 3
                                    3 1
                                    1 1
                                    2 4""")

        engine = GameEngine(path)

        self.assertEqual(engine.n, 4)
        self.assertEqual(engine.k, 3)
        self.assertEqual(engine.m, 6)
        self.assertEqual(len(engine.pieces), 6)
        self.assertEqual(engine.pieces[0], (1, 2))

    def test_rechaza_archivo_mal_formado(self):
        # Crear un archivo de instancia mal formado y verificar que se lance un ValueError.
        path = self._write_instance("""4 3
                                    6
                                    1 2
                                    """)

        with self.assertRaises(ValueError):
            GameEngine(path)

    def test_validacion_de_n_k_m(self):
        # Probar que se rechacen valores inválidos de n, k y m.
        invalid_cases = ["0 3\n4\n1 2\n2 3\n3 4\n4 5\n",
                        "4 0\n4\n1 2\n2 3\n3 4\n4 5\n",
                        "4 3\n0\n",]

        for content in invalid_cases:
            with self.subTest(content=content):
                path = self._write_instance(content)
                with self.assertRaises(ValueError):
                    GameEngine(path)

    def test_fichas_fuera_de_rango_o_invalidas(self):
        # Probar que se rechacen fichas con colores o valores fuera de rango.
        invalid_cases = ["""# TileUp
                        4 3
                        2
                        0 2
                        1 0""",
                        """# TileUp
                        4 3
                        2
                        4 2
                        1 1""",]

        for content in invalid_cases:
            with self.subTest(content=content):
                path = self._write_instance(content)
                with self.assertRaises(ValueError):
                    GameEngine(path)

    def test_colocacion_en_casilla_vacia(self):
        # Probar que se pueda colocar una ficha en una casilla vacía y que el estado del tablero se actualice correctamente.
        path = self._write_instance("""# TileUp
                                    4 3
                                    2
                                    1 2
                                    2 1""")
        
        engine = GameEngine(path)
        piece = engine.get_next_piece()

        engine.update_board(0, 0, piece)

        self.assertEqual(engine.board[0][0], (1, 2))
        self.assertTrue(engine.is_valid_position(0, 1))

    def test_colocacion_en_casilla_ocupada(self):
        # Probar que se lance un ValueError al intentar colocar una ficha en una casilla ocupada.
        path = self._write_instance("""# TileUp
                                    4 3
                                    2
                                    1 2
                                    2 1""")
        
        engine = GameEngine(path)
        engine.update_board(0, 0, engine.get_next_piece())

        self.assertFalse(engine.is_valid_position(0, 0))

        next_state = engine.get_state()
        with self.assertRaises(ValueError):
            engine.update_state(next_state, (0, 0))

    def test_fusion_cuando_mismo_color(self):
        # Probar que se fusionen correctamente las fichas cuando tienen el mismo color.
        path = self._write_instance("""# TileUp
                                    4 3
                                    3
                                    1 2
                                    1 3
                                    1 4""")
        
        engine = GameEngine(path)
        engine.board[0][0] = (1, 2)

        engine.update_board(0, 1, (1, 4))

        self.assertIsNone(engine.board[0][0])
        self.assertEqual(engine.board[0][1], (1, 6))

    def test_no_hay_fusion_con_color_distinto(self):
        # Probar que no se fusionen fichas de colores distintos.
        path = self._write_instance("""# TileUp
                                    4 3
                                    2
                                    1 2
                                    2 1""")
        
        engine = GameEngine(path)
        engine.board[0][0] = (1, 2)

        engine.update_board(0, 1, (2, 1))

        self.assertEqual(engine.board[0][0], (1, 2))
        self.assertEqual(engine.board[0][1], (2, 1))

    def test_secuencia_de_piezas_se_consume_en_orden(self):
        # Probar que las piezas se consuman en el orden correcto y que get_next_piece devuelva la pieza correcta.
        path = self._write_instance("""# TileUp
                                    4 3
                                    3
                                    1 2
                                    2 1
                                    1 3""")
        
        engine = GameEngine(path)

        self.assertEqual(engine.get_next_piece(), (1, 2))
        engine.next_piece_index = 1
        self.assertEqual(engine.get_next_piece(), (2, 1))

    def test_victory_y_defeat(self):
        # Probar que se detecte correctamente la victoria y la derrota.
        path = self._write_instance("""# TileUp
                                    2 1
                                    2
                                    1 2
                                    1 3""")
        engine = GameEngine(path)
        engine.next_piece_index = engine.m
        self.assertTrue(engine.is_victory())

        engine = GameEngine(path)
        engine.board = [[(1, 1), (1, 1)], [(1, 1), (1, 1)]]
        engine.next_piece_index = 0
        self.assertTrue(engine.is_defeat())


if __name__ == "__main__":
    unittest.main()
