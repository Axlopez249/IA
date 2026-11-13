# Simulador de ecosistema

Simulador 2D de herbivoros y carnivoros en Python. El nucleo del mundo no depende de redes neuronales ni de supervisores, pero expone puntos de extension para incorporarlos sin reescribir las reglas basicas.

## Ejecutar

Desde esta carpeta:

```powershell
python main.py
```

La simulacion imprime metricas cada diez pasos. Para abrir una ventana 2D animada:

```powershell
python main.py --visual --steps 100
```

Para entrenar las políticas neuronales por separado y guardar sus pesos:

```powershell
python train_policies.py --output checkpoints --epochs 10
python main.py --neural --steps 100
```

Para cumplir el protocolo mínimo de evaluación, entrena tres semillas:

```powershell
python train_policies.py --output checkpoints --epochs 10 --seeds 1 2 3
python benchmark.py --checkpoints checkpoints --seeds 1 2 3
python plot_results.py --results checkpoints --output results
```

El benchmark compara la política aleatoria, la heurística y REINFORCE. El
resultado se presenta como media +/- desviación estándar entre semillas.
Cada semilla guarda sus recompensas, longitudes y pérdidas en
`checkpoints/seed-N/training_results.json`. `plot_results.py` lee esos datos,
calcula la media y la desviación estándar por episodio para recompensa,
longitud y éxito, y genera
`results/learning_curves.png`.

El entrenamiento utiliza REINFORCE: cada episodio muestrea acciones de la
política, calcula recompensas y actualiza la red usando los retornos
descontados. No utiliza las acciones de `RuleBasedPolicy` como etiquetas.

## Formulación del MDP (Etapa 2)

- **Estado:** vector local normalizado de 20 valores: energía, edad, objetivos
  visibles, cantidades cercanas, comida visible, posición relativa y especie.
  El agente no recibe el mapa completo ni el estado interno de otros animales.
- **Acciones:** espacio discreto. Cada especie dispone de cinco acciones válidas:
  movimiento, descanso, huida, reproducción y una acción propia de su especie
  (`EAT` para herbívoros o `HUNT` para carnívoros).
- **Recompensa:** cambio de energía, una bonificación pequeña por permanecer
  vivo, penalización por morir y bonificaciones por caza y nacimiento. Esto es
  reward shaping y busca premiar supervivencia y estabilidad ecológica.
- **Fin del episodio:** muerte del animal controlado o llegada a `max_steps`.
- **Descuento:** `gamma=0.99`, porque las decisiones actuales deben considerar
  consecuencias cercanas de varios pasos sin hacer que las recompensas lejanas
  dominen el episodio.

La comparación mínima de la etapa usa tres referencias: `RandomPolicy`, que
elige uniformemente; `RuleBasedPolicy`, que representa una heurística manual; y
la política neuronal entrenada con REINFORCE. Los resultados deben repetirse
con las semillas 1, 2 y 3 y reportarse como media ± desviación estándar.

El entrenamiento genera dos archivos:

- `checkpoints/latest.json`: última época completada.
- `checkpoints/best.json`: época con mejor desempeño en una simulación de evaluación.

La puntuación combina supervivencia (40%), energía promedio (25%), estabilidad
poblacional (20%), nacimientos (10%) y cacerías (5%). Cada archivo conserva
también la época, la puntuación y las métricas de evaluación.

`main.py --neural` carga automáticamente `checkpoints/best.json` si existe y
guarda la ejecución terminada en `checkpoints/latest.json`. También se pueden
indicar rutas explícitas con `--policy-file` y `--save-policy-file`.

Para reanudar el entrenamiento:

```powershell
python train_policies.py --output checkpoints --resume checkpoints/latest.json
```

Para ejecutar una política guardada:

```powershell
python main.py --resume --steps 100
python main.py --load best --steps 100
```

`--resume` carga `checkpoints/latest.json`, mientras que `--load best` carga
`checkpoints/best.json` sin exploración. Si se usa solamente `--neural`, la
red se inicializa con pesos aleatorios.

La visualizacion grafica requiere `matplotlib`. La terminal se reserva para las metricas de la simulacion y no muestra una representacion alternativa del mapa.

## Pruebas

```powershell
python -m unittest discover -v
```

## Configuracion de la Fase 1

Los valores se encuentran en `SimulationConfig` dentro de `config.py`. Se pueden modificar al crear una configuracion para experimentar sin cambiar las reglas del mundo:

| Parametro | Funcion |
| --- | --- |
| `width`, `height` | Dimensiones del mapa. |
| `initial_herbivores`, `initial_carnivores` | Poblaciones iniciales. |
| `initial_food` | Cantidad inicial de comida. |
| `food_regrowth_rate` | Probabilidad de regeneracion de comida. |
| `initial_energy`, `max_energy` | Energia inicial y limite de referencia. |
| `movement_cost`, `hunger_cost` | Costes energeticos por accion. |
| `max_age` | Edad a partir de la cual muere un animal. |
| `perception_radius` | Distancia maxima para percibir objetivos. |
| `seed` | Semilla para reproducir una simulacion. |

La configuracion rechaza dimensiones no positivas, cantidades negativas, tasas fuera de `0.0` a `1.0` y costes energeticos negativos.

## Estructura

- `config.py`: parametros configurables del mundo.
- `environment/`: mapa, recursos y ciclo de simulacion.
- `agents/`: estado individual y acciones.
- `policies/`: decisiones individuales basadas en reglas o redes.
- `supervisors/`: contrato y objetivos colectivos. Los supervisores son opcionales.
- `metrics/`: resumen serializable del estado del mundo.
- `visualization/`: ventana 2D con matplotlib, independiente de la logica del mundo.
- `learning/`: observaciones, recompensas y prototipos de entrenamiento.
- `tests/`: pruebas de las fases implementadas y de los contratos de extension.

## Contratos de extension

`World` acepta un diccionario opcional de supervisores por especie. En cada paso consulta una vez a cada supervisor activo y guarda el `Objective` elegido en los animales de esa especie. Las políticas actuales consultan el objetivo mediante `animal.objective`: el supervisor puede
priorizar supervivencia, búsqueda de alimento, caza o reproducción antes de que la política
individual tome su decisión.

La politica individual sigue usando `choose_action(animal, world)`, por lo que las politicas basadas en reglas y las neuronales existentes mantienen compatibilidad.
