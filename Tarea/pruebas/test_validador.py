import os
import sys
import tempfile
import unittest

# Agregar el directorio raíz al path para poder importar el validador.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from validador import SolutionValidator


class TestSolutionValidator(unittest.TestCase):
    def _write_instance(self, content):
        # Crear un archivo temporal para la instancia de prueba.
        temp_dir = tempfile.mkdtemp(prefix="tileup_validator_")
        path = os.path.join(temp_dir, "instancia.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def _write_solution(self, directory, lines):
        # Crear un archivo temporal para la solución de prueba.
        path = os.path.join(directory, "solucion.txt")
        with open(path, "w", encoding="utf-8") as handle:
            for line in lines:
                handle.write(f"{line}\n")
        return path

    def test_solucion_valida_es_aceptada(self):
        # Crear una instancia y una solución válidas.
        instance_path = self._write_instance(
            """# TileUp
                4 3
                6
                1 2
                2 1
                1 3
                3 1
                1 1
                2 4""")
        directory = os.path.dirname(instance_path)
        solution_path = self._write_solution(directory, ["0 0 0", 
                                                        "1 1 1", 
                                                        "2 0 1", 
                                                        "3 2 2", 
                                                        "4 0 2", 
                                                        "5 1 2"])

        validator = SolutionValidator(instance_path)
        metrics = validator.validate(solution_path)

        self.assertIn("colocadas", metrics)
        self.assertEqual(metrics["colocadas"], 6)

    def test_movimiento_fuera_de_rango_rechazado(self):
        # Crear una instancia y una solución con un movimiento fuera de rango.
        instance_path = self._write_instance(
            """# TileUp
                4 3
                6
                1 2
                2 1
                1 3
                3 1
                1 1
                2 4""")
        directory = os.path.dirname(instance_path)
        solution_path = self._write_solution(directory, ["0 4 0", "1 0 1", "2 1 0"])

        validator = SolutionValidator(instance_path)
        with self.assertRaises(ValueError):
            validator.validate(solution_path)

    def test_casilla_ocupada_rechazada(self):
        # Crear una instancia y una solución que intente colocar una ficha en una casilla ocupada.
        instance_path = self._write_instance(
            """# TileUp
                4 3
                6
                1 2
                2 1
                1 3
                3 1
                1 1
                2 4""")
        directory = os.path.dirname(instance_path)
        solution_path = self._write_solution(directory, ["0 0 0", "1 0 0", "2 1 0"])

        validator = SolutionValidator(instance_path)
        with self.assertRaises(ValueError):
            validator.validate(solution_path)

    def test_indice_incorrecto_rechazado(self):
        # Crear una instancia y una solución que intente colocar una ficha con un índice incorrecto.
        instance_path = self._write_instance(
            """# TileUp
                4 3
                6
                1 2
                2 1
                1 3
                3 1
                1 1
                2 4""")
        directory = os.path.dirname(instance_path)
        solution_path = self._write_solution(directory, ["1 0 0", "0 0 1", "2 1 0"])

        validator = SolutionValidator(instance_path)
        with self.assertRaises(ValueError):
            validator.validate(solution_path)

    def test_formato_de_solucion_mal_escrito_rechazado(self):
        # Crear una instancia y una solución con formato incorrecto.
        instance_path = self._write_instance(
            """# TileUp
                4 3
                6
                1 2
                2 1
                1 3
                3 1
                1 1
                2 4""")
        directory = os.path.dirname(instance_path)
        solution_path = self._write_solution(directory, ["0 0", "1 0 1", "2 1 0"])

        validator = SolutionValidator(instance_path)
        with self.assertRaises(ValueError):
            validator.validate(solution_path)


if __name__ == "__main__":
    unittest.main()
