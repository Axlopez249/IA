# informe con la formulación de ambos agentes

## 1. Agente de Búsqueda (A*)

El agente de búsqueda fue implementado utilizando el algoritmo A*, garantizando la exploración de los caminos más prometedores hacia la meta.

- **Representación del Estado:** Una estructura que contiene la matriz del tablero actual, el índice de la siguiente ficha a colocar y la secuencia total de fichas de la instancia. Se hashea convirtiendo la matriz en tuplas inmutables para el registro de estados visitados y prevención de ciclos.
- **Operador de Sucesión:** Consiste en seleccionar una celda vacía (`get_valid_actions`) y simular la colocación de la ficha actual, resolviendo todas las reglas de fusión ortogonal. Este operador genera un nuevo estado clonado sin alterar el motor real de la partida.
- **Costo de la acción $g(n)$:** Se define como la cantidad total de celdas ocupadas en el tablero en el estado actual. Entre menos celdas ocupadas, menor es el costo.
- **Prueba de Meta:** Se verifica si la profundidad del nodo (cantidad de fichas colocadas) es igual o mayor a la cantidad total de fichas de la instancia ($M$).
- **Heurística $h(n)$:** Se calcula como la cantidad de fichas restantes por colocar en el tablero (`M - next_piece_index`).
- **Admisibilidad de la Heurística:** Esta heurística no es admisible. Asume de manera pesimista que cada ficha restante por colocar ocupará obligatoriamente una celda nueva, lo cual sobreestima el costo real (ya que las reglas de fusión del juego permiten liberar celdas al agrupar colores). Al utilizar esta heurística, se renuncia a la garantía matemática de encontrar la solución óptima absoluta (el tablero con el mínimo número de celdas ocupadas). Se tomó esta decisión técnica para guiar la búsqueda de forma agresiva hacia la victoria y evitar que el agente agote el límite de tiempo explorando todas las combinaciones tempranas, permitiendo así resolver instancias de mayor tamaño.

## 2. Agente Evolutivo

El algoritmo genético fue diseñado para evolucionar un plan de movimientos legales, optimizando la cantidad de fichas colocadas y el espacio libre.

- **Representación del Individuo:** Un cromosoma compuesto por una lista de números de punto flotante (genes) entre `0.0` y `1.0`. La longitud del cromosoma es igual a la cantidad de fichas restantes. Durante la simulación, cada gen se multiplica por el total de acciones legales disponibles en ese turno para obtener un índice válido, garantizando que el individuo solo genere movimientos legales.
- **Función de Aptitud (Fitness):** Diseñada para priorizar la victoria ante todo. La aptitud se calcula multiplicando la cantidad de fichas logradas por un factor masivo (`fichas_colocadas * 1.000.000`) y sumándole la cantidad de celdas que quedan libres. 
- **Mecanismo de Selección:** Se implementa un modelo de selección por truncamiento con elitismo. La población se ordena de mayor a menor aptitud y se selecciona un subconjunto de los 20 mejores individuos (`selection_size`) para la reproducción. El mejor individuo histórico global se resguarda siempre.
- **Operadores de Variación:**
    - **Cruce (Crossover):** De un solo punto. Se elige un índice aleatorio para dividir los cromosomas de dos padres seleccionados; el hijo hereda la primera mitad del Padre 1 y la segunda del Padre 2.
    - **Mutación:** Con una probabilidad del 10% (`mutation_rate = 0.10`), se selecciona un gen aleatorio del hijo y se reemplaza por un nuevo número flotante, inyectando diversidad en la exploración del tablero.
- **Política de Reemplazo:** Generacional. Los descendientes creados reemplazan en su totalidad a la población de la generación anterior, manteniendo un tamaño de población constante de 100 individuos.
- **Criterio de Paro:** El algoritmo se detiene si se agota el límite de tiempo seguro (`time_limit` - 2%) o si la población converge a un estado sin movimientos legales posibles.

**Procedimiento de fijación de parámetros:**
Los parámetros (`population_size = 100`, `selection_size = 20`, `mutation_rate = 0.10`) se fijaron mediante experimentación iterativa. Se observó que poblaciones mayores a 100 ralentizaban excesivamente las simulaciones por el costo del motor, provocando que el algoritmo realizara muy pocas generaciones antes del límite de tiempo. Una tasa de mutación del 10% demostró el equilibrio ideal para escapar de óptimos locales (atascos rápidos en el tablero) sin destruir las buenas secuencias genéticas logradas por el cruce.

## 3. Comparación Experimental

Para comparar el rendimiento de ambos algoritmos, se ejecutaron 6 configuraciones distintas de instancias ($N$, $K$, $M$), corriendo 3 semillas diferentes por cada configuración para medir la dispersión.

> **Nota: Hay que pegar aquí una tabla resumen basándose en el archivo `resumen.csv` que genera el script `comparacion_experimental.py`. Mencionar brevemente cuál agente logró colocar más fichas en las instancias más difíciles, cuál ocupó menos celdas y la diferencia en el tiempo de cómputo y nodos/evaluaciones expandidas.**

## 4. Estudio de Escalabilidad (Módulo de Grupos de 3)

Se implementó una batería de pruebas automatizada (`moduloExtra.py`) parametrizada para recorrer distintas configuraciones incrementales de tablero ($N$) y variedad de colores ($K$), manteniendo una cantidad fija de fichas ($M$). 

**Resultados y Degradación de los Agentes:**

> **Nota: Hay que pegar aquí directamente el contenido textual que el programa genera en `reporte/reporte_escalabilidad.txt`. Luego, añadir un pequeño párrafo y una captura de gráfica generada en Python analizando en qué régimen exacto el agente A* comienza a agotar el límite de tiempo y deja de encontrar la solución completa, y cómo se comporta el agente evolutivo bajo esa misma presión de tamaño y colores.**