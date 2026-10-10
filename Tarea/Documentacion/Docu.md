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
Para comparar el rendimiento de ambos algoritmos, se ejecutaron 6 configuraciones distintas de instancias ($N$, $K$, $M$), corriendo 3 semillas diferentes por cada configuración para medir la dispersión y consistencia de los resultados.

A continuación se presenta el resumen de las métricas (Media ± Desviación Estándar) agrupadas por instancia y agente:

| Instancia | N | K | M | Agente | Colocadas | Ocupadas | Tiempo (s) | Esfuerzo (Nodos/Eval) |
| :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | 3 | 2 | 6 | search | 6.0 ± 0.0 | 2.0 ± 0.0 | 0.0004 ± 0.0000 | 7.0 ± 0.0 |
| 1 | 3 | 2 | 6 | evolution | 6.0 ± 0.0 | 2.0 ± 0.0 | 4.9012 ± 0.0008 | 34066.7 ± 986.6 |
| 2 | 3 | 3 | 8 | search | 8.0 ± 0.0 | 3.0 ± 0.0 | 0.0005 ± 0.0000 | 9.0 ± 0.0 |
| 2 | 3 | 3 | 8 | evolution | 8.0 ± 0.0 | 3.0 ± 0.0 | 4.9029 ± 0.0014 | 27733.3 ± 461.9 |
| 3 | 4 | 2 | 8 | search | 8.0 ± 0.0 | 2.0 ± 0.0 | 0.0009 ± 0.0001 | 9.0 ± 0.0 |
| 3 | 4 | 2 | 8 | evolution | 8.0 ± 0.0 | 2.0 ± 0.0 | 4.9019 ± 0.0013 | 24000.0 ± 173.2 |
| 4 | 4 | 3 | 10 | search | 10.0 ± 0.0 | 3.0 ± 0.0 | 0.0010 ± 0.0000 | 11.0 ± 0.0 |
| 4 | 4 | 3 | 10 | evolution | 10.0 ± 0.0 | 3.0 ± 0.0 | 4.9030 ± 0.0016 | 20100.0 ± 400.0 |
| 5 | 5 | 3 | 10 | search | 10.0 ± 0.0 | 3.0 ± 0.0 | 0.0016 ± 0.0000 | 11.0 ± 0.0 |
| 5 | 5 | 3 | 10 | evolution | 10.0 ± 0.0 | 3.3 ± 0.58 | 4.9032 ± 0.0025 | 17533.3 ± 152.8 |
| 6 | 5 | 4 | 12 | search | 12.0 ± 0.0 | 4.0 ± 0.0 | 0.0019 ± 0.0001 | 13.0 ± 0.0 |
| 6 | 5 | 4 | 12 | evolution | 12.0 ± 0.0 | 4.3 ± 0.58 | 4.9014 ± 0.0004 | 14700.0 ± 692.8 |

**Análisis de Resultados:**
Observando los datos recolectados, el agente basado en búsqueda (A*) demuestra ser superior en estas escalas del problema. En todos los escenarios A* logra encontrar la solución óptima en menos de 0.002 segundos, expandiendo un máximo de 13 nodos (Instancia 6). 

Por el contrario, el agente evolutivo consume la totalidad del límite de tiempo establecido (~4.9 segundos) realizando decenas de miles de evaluaciones de aptitud. Aunque el agente evolutivo logra colocar todas las fichas en las 6 instancias, sufre una ligera degradación en la optimización del espacio a medida que el tablero crece: en las instancias 5 y 6, el evolutivo deja un promedio de 3.3 y 4.3 celdas ocupadas respectivamente, mientras que A* logra consolidar mejor las fusiones dejando el tablero con solo 3 y 4 celdas ocupadas de manera consistente.

## 4. Estudio de Escalabilidad (Módulo de Grupos de 3)
Se implementó una batería de pruebas automatizada (`moduloExtra.py`) parametrizada para recorrer distintas configuraciones incrementales de tablero ($N$) y variedad de colores ($K$), manteniendo una cantidad fija de fichas ($M=10$) con 3 semillas por configuración.

**Resultados Generales del Reporte:**
- Ejecuciones: 27 por agente.
- Ejecuciones incompletas: 6 por agente (22.22%).
- Impacto de variables: El parámetro que más incrementa la cantidad de celdas ocupadas en promedio es K (variedad de colores) con una variación de 3.89, frente a la variación de 1.33 provocada por el tamaño del tablero ($N$).

__Comportamiento del Agente de Búsqueda:__
- Celdas ocupadas promedio por $N$: $N=2$ (3.33 ± 1.00), $N=4$ (4.67 ± 2.60), $N=8$ (4.44 ± 2.24).
- Celdas ocupadas promedio por $K$: $K=2$ (2.00), $K=4$ (4.22), $K=8$ (6.22).
- Punto de quiebre: Presenta ejecuciones incompletas a partir de $N=2, K=4$.

**Comportamiento del Agente Evolutivo:**
- Celdas ocupadas promedio por $N$: $N=2$ (3.33 ± 1.00), $N=4$ (4.44 ± 2.24), $N=8$ (4.89 ± 1.76).
- Celdas ocupadas promedio por $K$: $K=2$ (2.44), $K=4$ (4.22), $K=8$ (6.00).
- Punto de quiebre: Al igual que A*, presenta exactamente 6 ejecuciones incompletas en el mismo conjunto de instancias.

**Análisis del Régimen de Degradación:**
Los datos revelan que la variable que verdaderamente domina la dificultad del problema no es el tamaño del tablero ($N$), sino la cantidad de colores ($K$). Al aumentar los colores de 2 a 8, la cantidad de celdas que quedan ocupadas en el tablero prácticamente se triplica (pasando de ~2.00 a ~6.22). Esto ocurre porque una mayor variedad de estos reduce drásticamente la probabilidad de colocar fichas adyacentes del mismo color, limitando las fusiones y saturando el tablero rápidamente. Ademas,ambos agentes fracasan exactamente en el mismo régimen ($N=2, K \ge 4$). Esto indica que la limitante en este caso no es la capacidad del algoritmo A* o del agente evolutivo (como exceder el límite de tiempo o quedarse atascado en mínimos locales), sino un límite físico y espacial del problema: en un tablero de $2 \times 2$ (4 celdas totales) con $M=10$ fichas a colocar y una alta variedad de colores, el tablero se satura con colores incompatibles antes de poder consumirse la secuencia completa, desencadenando una derrota determinista insalvable para cualquier inteligencia artificial.

> **Nota: Hay que generar un gráfico en Excel usando los promedios de celdas ocupadas por $K$ (2, 4 y 8) para ambos agentes e insertar la imagen justo debajo de este párrafo para respaldar visualmente el análisis.**