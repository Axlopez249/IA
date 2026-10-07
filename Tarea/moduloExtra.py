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
                    self.execute_agent(
                        "search",
                        ruta,
                        seed,
                        n,
                        k,
                        self.m,
                        seed,
                        self.time,
                        solution_path=os.path.join(
                            modulo_dir, f"solution_search_{nombre_archivo}"
                        ),
                    )
                    self.execute_agent(
                        "evolution",
                        ruta,
                        seed,
                        n,
                        k,
                        self.m,
                        seed,
                        self.time,
                        solution_path=os.path.join(
                            modulo_dir, f"solution_evolution_{nombre_archivo}"
                        ),
                    )

        # Se llama a la funcion para obtener los datos de cada agente para cada configuración
        self.obtener_datos_agentes()

        # Se llama a la funcion para generar un csv con los datos obtenidos de cada agente para cada configuración
        self.generar_csv()

        # Se genera el reporte y la gráfica a partir de los datos obtenidos.
        self.generar_reporte()

    def obtener_datos_agentes(self):
        """
        Recorre los archivos de solución generados y guarda sus métricas.
        """
        self.datosSearch = []
        self.datosEvo = []

        for n, k, m, seed, ruta_instancia in self.configuraciones:
            nombre_archivo = os.path.basename(ruta_instancia)

            for nombre_agente, datos_agente in (("search", self.datosSearch),("evolution", self.datosEvo),
            ):
                # Nombre del archivo de solución generado por el agente
                solution_path = os.path.join(
                    self.base_dir,
                    "modulo",
                    f"solution_{nombre_agente}_{nombre_archivo}",
                )

                # Se abre el archivo de solución y se leen las métricas del agente
                try:
                    with open(solution_path, "r", encoding="utf-8") as file:
                        lineas = file.readlines()
                except OSError as error:
                    raise ValueError(
                        f"No se pudo leer el archivo de solución: "
                        f"{solution_path}"
                    ) from error

                resumen = next(
                    (
                        linea.strip()
                        for linea in reversed(lineas)
                        if linea.strip().startswith("#")
                    ),
                    None,
                )
                if resumen is None:
                    raise ValueError(
                        f"El archivo de solución no contiene métricas: "
                        f"{solution_path}"
                    )

                # Diccionario para almacenar las métricas del agente
                metricas = {}
                for clave, valor in re.findall(
                    r"([A-Za-z_]+)\s*=\s*(-?\d+)",
                    resumen.lstrip("#"),
                ):
                    metricas[clave] = int(valor)

                metricas_requeridas = ("colocadas", "ocupadas", "mayor")
                faltantes = [
                    clave for clave in metricas_requeridas
                    if clave not in metricas
                ]
                if faltantes:
                    raise ValueError(
                        f"Faltan métricas {faltantes} en {solution_path}"
                    )

                datos_agente.append(
                    {
                        "agente": nombre_agente,
                        "n": n,
                        "k": k,
                        "m": m,
                        "seed": seed,
                        "solution_path": solution_path,
                        "colocadas": metricas["colocadas"],
                        "ocupadas": metricas["ocupadas"],
                        "mayor": metricas["mayor"],
                    }
                )

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
        Genera un reporte textual y una gráfica SVG con las tendencias.

        Una ejecución se considera incompleta cuando colocadas < M. El tiempo
        exacto no está disponible en el archivo de solución, por lo que esta
        medida identifica el comportamiento observado al agotar el límite.
        """
        datos = self.datosSearch + self.datosEvo
        if not datos:
            raise ValueError("No hay datos para generar el reporte.")

        ruta_reporte = os.path.join(
            self.base_dir, "reporte", "reporte_escalabilidad.txt"
        )
        ruta_grafica = os.path.join(
            self.base_dir, "reporte", "grafica_escalabilidad.svg"
        )
        os.makedirs(os.path.dirname(ruta_reporte), exist_ok=True)
        lineas = [
            "REPORTE DE ESCALABILIDAD DE TILEUP",
            "=================================",
            "",
            "Criterio: una ejecución se considera incompleta si colocadas < M.",
            "El tiempo exacto no se conserva en los archivos de solución;",
            "por ello, la terminación se analiza mediante este criterio.",
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
            self._generar_grafica_svg(datos, ruta_grafica)
        except OSError as error:
            raise ValueError(
                "No se pudo escribir el reporte de escalabilidad."
            ) from error

        print(f"Reporte generado: {ruta_reporte}")
        print(f"Gráfica generada: {ruta_grafica}")

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

    def _generar_grafica_svg(self, datos, ruta_grafica):
        """
        Genera una gráfica SVG de celdas ocupadas promedio según N.
        """
        por_agente = {}
        # Se toman en cuenta los 2 agentes y se van recorriendo los datos
        for agente in ("search", "evolution"):
            grupos = {}
            # Se toma cada dato del agente y se agrupa por N para calcular el promedio de celdas ocupadas
            for dato in datos:
                # Si el agente coincide con el dato, se agrega al grupo correspondiente por N
                if dato["agente"] == agente:
                    # Por N agrega cantidad de celdas ocupadas al grupo correspondiente
                    grupos.setdefault(dato["n"], []).append(dato["ocupadas"])
            # Cambia de llave, valor a pares pero manteniendo la llave como N y el valor como promedio de celdas ocupadas
            por_agente[agente] = {
                n: statistics.mean(valores) for n, valores in grupos.items()
            }

        # Esto es para generar la gráfica SVG, se calcula el ancho y alto de la gráfica, el margen, el máximo valor de celdas ocupadas y la escala para los ejes X e Y
        valores = [
            valor for grupos in por_agente.values() for valor in grupos.values()
        ]
        # Se obtienen los valores de N y se ordenan para poder graficar correctamente
        ns = sorted(
            {
                n for grupos in por_agente.values()
                for n in grupos
            }
        )
        ancho, alto = 800, 500
        margen = 70
        maximo = max(valores) if valores else 1
        escala_x = (ancho - 2 * margen) / max(1, len(ns) - 1)
        escala_y = (alto - 2 * margen) / maximo

        elementos = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" '
            f'height="{alto}" viewBox="0 0 {ancho} {alto}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<text x="70" y="30" font-size="18">'
            'Celdas ocupadas promedio según N</text>',
            f'<line x1="{margen}" y1="{alto - margen}" x2="{ancho - margen}" '
            f'y2="{alto - margen}" stroke="black"/>',
            f'<line x1="{margen}" y1="{margen}" x2="{margen}" '
            f'y2="{alto - margen}" stroke="black"/>',
        ]

        colores = {"search": "#1f77b4", "evolution": "#d62728"}
        for agente, grupos in por_agente.items():
            puntos = []
            for indice, n in enumerate(ns):
                if n not in grupos:
                    continue
                x = margen + indice * escala_x
                y = alto - margen - grupos[n] * escala_y
                puntos.append(f"{x:.2f},{y:.2f}")
                elementos.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" '
                    f'fill="{colores[agente]}"/>'
                )
            if puntos:
                elementos.append(
                    f'<polyline points="{" ".join(puntos)}" fill="none" '
                    f'stroke="{colores[agente]}" stroke-width="2"/>'
                )

        elementos.extend(
            [
                f'<text x="{ancho // 2}" y="{alto - 15}" '
                'text-anchor="middle">N</text>',
                '<text x="15" y="250" transform="rotate(-90 15 250)">'
                'Celdas ocupadas</text>',
                '<text x="600" y="55" fill="#1f77b4">search</text>',
                '<text x="680" y="55" fill="#d62728">evolution</text>',
                "</svg>",
            ]
        )
        with open(ruta_grafica, "w", encoding="utf-8") as file:
            file.write("\n".join(elementos))


    def execute_agent(
        self,
        nombre_agente,
        ruta_instancia,
        semilla,
        n,
        k,
        m,
        seed,
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
            subprocess.run(
                comando,
                check=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError(
                f"No se pudo ejecutar el agente '{nombre_agente}' "
                f"para la instancia {ruta_instancia}."
            ) from error


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