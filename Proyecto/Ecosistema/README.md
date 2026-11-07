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

`World` acepta un diccionario opcional de supervisores por especie. En cada paso consulta una vez a cada supervisor activo y guarda el `Objective` elegido en los animales de esa especie. Las politicas actuales no necesitan usarlo todavía; una politica futura puede leer `animal.objective` sin cambiar el ciclo del mundo.

La politica individual sigue usando `choose_action(animal, world)`, por lo que las politicas basadas en reglas y las neuronales existentes mantienen compatibilidad.
