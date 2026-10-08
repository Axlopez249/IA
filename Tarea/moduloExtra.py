import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
from generador import InstanceGenerator

class ConfiguracionEscalabilidad:

    def __init__(self, cantidad_n, cantidad_k, m, cantidad_seeds):

        # Parámetros recibidos
        self.cantidad_n = cantidad_n
        self.cantidad_k = cantidad_k
        self.m = m
        self.cantidad_seeds = cantidad_seeds
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Valores que se generarán posteriormente
        self.valores_n = []
        self.valores_k = []
        self.semillas = []

        # Configuraciones que se generarán posteriormente
        self.configuraciones = []

        # Tiempo para cada agente
        self.time = 3

        # Datos de cada agente para cada configuración
        self.datosSearch = []
        self.datosEvo = []

    def validar(self):
        """
        Valida los parámetros recibidos para el estudio
        de escalabilidad.
        """

        # Cantidad de configuraciones de N
        if self.cantidad_n < 3:
            raise ValueError(
                "La cantidad de configuraciones de N debe ser "
                "mayor o igual a 3."
            )

        # Cantidad de configuraciones de K
        if self.cantidad_k < 3:
            raise ValueError(
                "La cantidad de configuraciones de K debe ser "
                "mayor o igual a 3."
            )

        # Cantidad de fichas
        if self.m <= 0:
            raise ValueError(
                "La cantidad de fichas M debe ser mayor que 0."
            )

        # Cantidad de semillas
        if self.cantidad_seeds < 3:
            raise ValueError(
                "La cantidad de semillas debe ser "
                "mayor o igual a 3."
            )

    def generar_valores_n(self):
        """
        Generará los diferentes valores de N.
        """
        self.valores_n = []
        for i in range(self.cantidad_n):
            self.valores_n.append(2 ** (i + 1))

        return self.valores_n

    def generar_valores_k(self):
        """
        Generará los diferentes valores de K.
        """
        self.valores_k = []
        for i in range(self.cantidad_k):
            self.valores_k.append(2 ** (i + 1))

        return self.valores_k

    def generar_semillas(self):
        """
        Generará las semillas utilizadas en el estudio.
        """
        self.semillas = []
        for i in range(self.cantidad_seeds):
            self.semillas.append(i)

        return self.semillas

    # Funcion que me crea las instancias
    def generar_configuraciones(self):
        """
    Generará todas las combinaciones de:

        N × K × seed

        M se mantiene fijo.
        """
        modulo_dir = os.path.join(self.base_dir, "modulo")
        os.makedirs(modulo_dir, exist_ok=True)

        for n in self.valores_n:
            for k in self.valores_k:
                for seed in self.semillas:
                    # Nombre de la instancia
                    nombre_archivo = (f"N{n}_K{k}_M{self.m}_seed{seed}.txt")

                    # Ruta de salida de la instancia
                    ruta = os.path.join(modulo_dir, nombre_archivo)

                    generador = InstanceGenerator(n, k, self.m, seed)
                    generador.write_instance(ruta)
                    self.configuraciones.append((n, k, self.m, seed, ruta))

                    # Ejecutar agentes para cada configuración
                    datos_agente = self.execute_agent(
                        "search",
                        ruta,
                        seed,
                        self.time,
                        solution_path=os.path.join(
                            modulo_dir, f"solution_search_{nombre_archivo}"
                        ),
                    )
                    self.datosSearch.append(
                        {
                            "agente": "search",
                            "n": n,
                            "k": k,
                            "m": self.m,
                            "seed": seed,
                            "solution_path": os.path.join(
                                modulo_dir, f"solution_search_{nombre_archivo}"
                            ),
                            **datos_agente,
                        }
                    )
                    datos_agente = self.execute_agent(
                        "evolution",
                        ruta,
                        seed,
                        self.time,
                        solution_path=os.path.join(
                            modulo_dir, f"solution_evolution_{nombre_archivo}"
                        ),
                    )
                    self.datosEvo.append(
                        {
                            "agente": "evolution",
                            "n": n,
                            "k": k,
                            "m": self.m,
                            "seed": seed,
                            "solution_path": os.path.join(
                                modulo_dir, f"solution_evolution_{nombre_archivo}"
                            ),
                            **datos_agente,
                        }
                    )

        # Se llama a la funcion para generar un csv con los datos obtenidos de cada agente para cada configuración
        self.generar_csv()

        # Se genera el reporte a partir de los datos obtenidos.
        self.generar_reporte()

    def generar_csv(self):
        """
        Genera un CSV con las métricas de todos los agentes y configuraciones.
        """
        datos = self.datosSearch + self.datosEvo
        ruta_csv = os.path.join(
            self.base_dir, "reporte", "datos_escalabilidad.csv"
        )
        os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
        campos = [
            "agente",
            "n",
            "k",
            "m",
            "seed",
            "solution_path",
            "colocadas",
            "ocupadas",
            "mayor",
            "tiempo",
            "esfuerzo",
        ]

        try:
            with open(ruta_csv, "w", newline="", encoding="utf-8") as file:
                escritor = csv.DictWriter(file, fieldnames=campos)
                escritor.writeheader()
                escritor.writerows(datos)
        except OSError as error:
            raise ValueError(
                f"No se pudo escribir el archivo CSV: {ruta_csv}"
            ) from error

        print(f"CSV generado: {ruta_csv}")

    def generar_reporte(self):
        """
        Genera un reporte textual con las tendencias.

        Una ejecución se considera incompleta cuando colocadas < M. Las
        métricas de tiempo se toman de la salida del subproceso.
        """
        datos = self.datosSearch + self.datosEvo
        if not datos:
            raise ValueError("No hay datos para generar el reporte.")

        ruta_reporte = os.path.join(
            self.base_dir, "reporte", "reporte_escalabilidad.txt"
        )
        os.makedirs(os.path.dirname(ruta_reporte), exist_ok=True)
        lineas = [
            "REPORTE DE ESCALABILIDAD DE TILEUP",
            "=================================",
            "",
            "Criterio: una ejecución se considera incompleta si colocadas < M.",
            "Las métricas y el tiempo se obtienen directamente de la salida",
            "capturada de cada subproceso.",
            "",
        ]

        # Se saca la informacion de cada agente y se calcula el promedio de celdas ocupadas por N y K
        for agente in ("search", "evolution"):
            datos_agente = [dato for dato in datos if dato["agente"] == agente]
            if not datos_agente:
                continue

            incompletas = [
                dato for dato in datos_agente
                if dato["colocadas"] < dato["m"]
            ]
            # Se calcula el porcentaje de ejecuciones incompletas por medio de
            # las acciones totales y las acciones incompletas, y se agrega al reporte
            porcentaje = 100 * len(incompletas) / len(datos_agente)
            lineas.append(
                f"{agente}: {len(datos_agente)} ejecuciones, "
                f"{len(incompletas)} incompletas ({porcentaje:.2f}%)."
            )

            # Se calcula el promedio de celdas ocupadas por N y se agrega al reporte
            por_n = {}
            for dato in datos_agente:
                por_n.setdefault(dato["n"], []).append(dato["ocupadas"])
            lineas.append("  Promedio de celdas ocupadas por N:")
            for n in sorted(por_n):
                valores = por_n[n]
                dispersion = (
                    statistics.stdev(valores) if len(valores) > 1 else 0
                )
                lineas.append(
                    f"    N={n}: promedio={statistics.mean(valores):.2f}, "
                    f"desviacion_entre_semillas={dispersion:.2f}"
                )

            # Se calcula el promedio de celdas ocupadas por K y se agrega al reporte
            por_k = {}
            for dato in datos_agente:
                por_k.setdefault(dato["k"], []).append(dato["ocupadas"])
            lineas.append("  Promedio de celdas ocupadas por K:")
            for k in sorted(por_k):
                lineas.append(
                    f"    K={k}: promedio={statistics.mean(por_k[k]):.2f}"
                )
            lineas.append("")

        # Se agrega la lectura comparativa de N, K y el régimen incompleto
        # Se llama a la función _interpretar_reporte para obtener las líneas de interpretación
        lineas.extend(self._interpretar_reporte(datos))

        try:
            with open(ruta_reporte, "w", encoding="utf-8") as file:
                file.write("\n".join(lineas) + "\n")
        except OSError as error:
            raise ValueError(
                "No se pudo escribir el reporte de escalabilidad."
            ) from error

        print(f"Reporte generado: {ruta_reporte}")

    def _interpretar_reporte(self, datos):
        """
        Agrega una lectura comparativa de N, K y el régimen incompleto.
        """
        lineas = ["LECTURA DEL RESULTADO", "====================="]
        promedios_n = {}
        promedios_k = {}
        for dato in datos:
            promedios_n.setdefault(dato["n"], []).append(dato["ocupadas"])
            promedios_k.setdefault(dato["k"], []).append(dato["ocupadas"])

        # Se sacan las variaciones de N y K para determinar cuál tiene mayor impacto en las celdas ocupadas promedio
        variacion_n = max(
            statistics.mean(valores) for valores in promedios_n.values()
        ) - min(
            statistics.mean(valores) for valores in promedios_n.values()
        )
        variacion_k = max(
            statistics.mean(valores) for valores in promedios_k.values()
        ) - min(
            statistics.mean(valores) for valores in promedios_k.values()
        )
        parametro = "N (tamaño del tablero)" if variacion_n >= variacion_k else "K (colores)"
        lineas.append(
            f"El parámetro que más cambia las celdas ocupadas en promedio es "
            f"{parametro}: variación por N={variacion_n:.2f}, "
            f"variación por K={variacion_k:.2f}."
        )

        # Se calcula el porcentaje de ejecuciones incompletas por agente
        incompletas_search = [
            dato for dato in datos
            if dato["agente"] == "search" and dato["colocadas"] < dato["m"]
        ]
        if incompletas_search:
            primera = min(
                incompletas_search,
                key=lambda dato: (dato["n"], dato["k"], dato["seed"]),
            )
            lineas.append(
                "El agente search presenta ejecuciones incompletas desde "
                f"N={primera['n']}, K={primera['k']} (seed={primera['seed']})."
            )
        else:
            lineas.append(
                "El agente search completa todas las ejecuciones observadas."
            )

        incompletas_evo = [
            dato for dato in datos
            if dato["agente"] == "evolution" and dato["colocadas"] < dato["m"]
        ]
        if incompletas_evo:
            lineas.append(
                f"El agente evolution tiene {len(incompletas_evo)} "
                "ejecuciones incompletas en el mismo conjunto."
            )
        else:
            lineas.append(
                "El agente evolution completa todas las ejecuciones observadas."
            )
        return lineas

    def execute_agent(
        self,
        nombre_agente,
        ruta_instancia,
        semilla,
        limite_tiempo,
        solution_path,
    ):
        """
        Ejecuta el agente con los parámetros proporcionados.
        """
        comando = [
            sys.executable,
            "main.py",
            ruta_instancia,
            "--agent",
            nombre_agente,
            "--seed",
            str(semilla),
            "--time-limit",
            str(limite_tiempo),
            "--output",
            solution_path,
        ]
        try:
            resultado = subprocess.run(
                comando,
                check=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError(
                f"No se pudo ejecutar el agente '{nombre_agente}' "
                f"para la instancia {ruta_instancia}."
            ) from error

        metricas = dict(
            re.findall(
                r"([A-Za-z_]+)\s*=\s*(-?\d+(?:\.\d+)?)",
                resultado.stdout,
            )
        )
        metricas_requeridas = ("colocadas", "ocupadas", "mayor", "tiempo", "esfuerzo")
        faltantes = [clave for clave in metricas_requeridas if clave not in metricas]
        if faltantes:
            raise ValueError(
                f"La salida del agente '{nombre_agente}' no contiene las "
                f"métricas requeridas: {faltantes}. Salida: {resultado.stdout!r}"
            )

        for clave in ("colocadas", "ocupadas", "mayor", "esfuerzo"):
            metricas[clave] = int(metricas[clave])
        metricas["tiempo"] = float(metricas["tiempo"])
        return metricas


def obtener_argumentos():
    """
    Obtiene los argumentos proporcionados desde la línea
    de comandos.
    """

    parser = argparse.ArgumentParser(description="Estudio de escalabilidad de TileUp.")

    parser.add_argument("cantidad_n", type=int,help="Cantidad de configuraciones diferentes de N.")

    parser.add_argument( "cantidad_k", type=int,help="Cantidad de configuraciones diferentes de K." )

    parser.add_argument("m",type=int,help="Cantidad fija de fichas M.")

    parser.add_argument("cantidad_seeds",type=int,help="Cantidad de semillas por configuración.")

    return parser.parse_args()


def main():

    # ==========================================
    # Obtener argumentos
    # ==========================================

    args = obtener_argumentos()

    # ==========================================
    # Crear configuración
    # ==========================================

    configuracion = ConfiguracionEscalabilidad(args.cantidad_n, args.cantidad_k, args.m, args.cantidad_seeds)
    # ==========================================
    # Validar parámetros
    # ==========================================

    configuracion.validar()

    # ==========================================
    # Generar valores de N, K y semillas
    # ==========================================

    configuracion.generar_valores_n()
    configuracion.generar_valores_k()
    configuracion.generar_semillas()
    configuracion.generar_configuraciones()

    # ==========================================
    # Información recibida
    # ==========================================



    print("Configuración del estudio de escalabilidad:")
    print(f"Cantidad de configuraciones de N: {configuracion.cantidad_n}")
    print(f"Cantidad de configuraciones de K: {configuracion.cantidad_k}")
    print(f"Cantidad fija de M: {configuracion.m}")
    print(f"Cantidad de semillas: {configuracion.cantidad_seeds}")


if __name__ == "__main__":
    main()