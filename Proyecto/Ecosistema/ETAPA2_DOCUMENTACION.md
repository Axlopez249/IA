# Etapa 2 — Formulación, entrenamiento y evaluación

## 1. Formulación del MDP

El entorno se modela como un proceso de decisión de Markov por individuo. En
cada paso, el agente recibe una observación local de 20 valores normalizados:

- energía y edad del individuo;
- distancia y dirección relativa a comida, depredadores o presas visibles;
- cantidad de individuos cercanos de la misma y otra especie;
- cantidad de comida visible;
- posición relativa a los límites del mapa;
- especie del individuo.

El agente no observa el mapa completo, recursos fuera de su radio de
percepción ni el estado interno completo de los demás individuos. Esta
restricción representa información parcial del entorno y evita entregar
información global que no estaría disponible para el animal.

El espacio de acciones es discreto. Cada especie tiene cinco acciones válidas:

- herbívoros: `MOVE`, `EAT`, `FLEE`, `REST`, `REPRODUCE`;
- carnívoros: `MOVE`, `HUNT`, `FLEE`, `REST`, `REPRODUCE`.

La red produce seis logits porque `EAT` y `HUNT` comparten una salida general,
pero la política enmascara la acción no válida para cada especie.

La recompensa implementada en `learning/rewards.py` es:

```text
r_t = (energía_t - energía_(t-1))
      + 0.05                         si el individuo sigue vivo
      - 10                          si muere en el paso
      + 3 × nuevas_cacerías
      + 2 × nuevos_nacimientos
      + 0.15                        si descansa con energía baja
      - 0.30                        si descansa con energía suficiente
      + 5                           si REPRODUCE produce una cría
```

El cambio de energía se normaliza por la mayor ganancia de comida o cacería.
Esta función utiliza reward shaping: la supervivencia y el cambio energético
favorecen la conservación del individuo, mientras que las bonificaciones de
cacería y nacimiento representan objetivos ecológicos del entorno. El descanso
solo se premia con energía baja para evitar que se convierta en la estrategia
dominante.

El episodio termina cuando muere el individuo controlado o cuando alcanza
`max_steps`. El horizonte experimental utilizado es de 50 pasos por episodio.
El factor de descuento es `gamma = 0.99`, de modo que las consecuencias futuras
cercanas influyen en la decisión sin dominar completamente el episodio.

El entorno también permite supervisión jerárquica opcional. El supervisor
observa la población viva de su especie y puede ordenar `SEARCH_FOOD`, `HUNT`,
`GROUP` o `SURVIVE`. `GROUP` dirige a los individuos elegibles hacia la pareja
reproductiva más cercana; la reproducción solo ocurre cuando ambos están en la
misma celda y cumplen edad y energía mínimas. El umbral energético actual es
`30`, con edad mínima `5`.

## 2. Baselines

Se comparan las siguientes políticas:

1. `RandomPolicy`: selecciona uniformemente una acción válida.
2. `RuleBasedPolicy`: prioriza huir, comer o cazar cuando corresponde, descansar
   con poca energía y moverse en los demás casos.
3. Política neuronal entrenada con REINFORCE.
4. Baselines de literatura:
   - Pihlakas et al. (2025): marco multiobjetivo de homeostasis y
     prevención de extinción por consumo desregulado.
   - Barton et al. (2018): recompensa media de captura de `13.70`,
     frente a `1.85` en políticas fijas.
   - Xu y Dang (2025): `99.9%` de éxito en persecución sobre una
     cuadrícula 2D.

## 3. Entrenamiento

El algoritmo utilizado es REINFORCE con retornos descontados. Es apropiado
porque el espacio de acciones es discreto y el entorno entrega recompensas
después de ejecutar trayectorias completas.

### Experimento principal de Etapa 2

Este es el experimento usado para la comparación final entre `RandomPolicy`,
`RuleBasedPolicy` y REINFORCE. Se ejecutó con cinco semillas independientes:

| Parámetro | Valor |
|---|---:|
| Semillas | `1, 2, 3, 4, 5` |
| Épocas | `10` |
| Episodios por época y especie | `50` |
| Episodios por especie y semilla | `500` |
| Pasos máximos por episodio | `50` |
| Tasa de aprendizaje | `0.01` |
| `gamma` | `0.99` |
| Episodios independientes de evaluación | `10` |

La exploración durante REINFORCE se realiza muestreando acciones desde la
distribución softmax de la política. La evaluación utiliza las políticas
guardadas y no actualiza sus pesos.

Los artefactos de este protocolo están en `experiments/stage2/`, incluyendo un
checkpoint para cada semilla y las tablas finales de evaluación.

Datos del experimento principal:

- hardware: AMD Ryzen 5 5500, placa Gigabyte B450M DS3H V2;
- versión de Python: `3.13.2`;
- tiempo total: `259.2 s`;
- semillas: `1, 2, 3, 4, 5`.

## 4. Protocolo de evaluación del experimento principal

Ejecutar:

```powershell
python run_experiments.py --output experiments/stage2 --epochs 10 --episodes 50 --steps-per-episode 50 --evaluation-episodes 10 --seeds 1 2 3 4 5
```

El comando genera:

- `training_metrics.csv`: recompensa, longitud, pérdida y éxito por episodio;
- `evaluation_metrics.csv`: resultados de las políticas aleatoria, heurística y
  neuronal;
- `training_curves.png`: curvas de entrenamiento con media y desviación
  estándar entre semillas;
- `evaluation_comparison.png`: comparación de baselines con barras de error;
- `run_metadata.txt`: configuración y tiempo de ejecución;
- checkpoints independientes para cada semilla.

## 5. Resultados del experimento principal

La siguiente tabla se calculó desde `evaluation_metrics.csv`, promediando
primero los diez episodios de cada semilla y reportando media ± desviación
estándar entre las cinco semillas:

| Política | Fitness medio ± desviación | Recompensa media ± desviación | Éxito medio ± desviación | Longitud media ± desviación |
|---|---:|---:|---:|---:|
| Aleatoria | `0.6240 ± 0.0132` | `62.0809 ± 6.3357` | `0.7463 ± 0.0283` | `28.16 ± 3.19` |
| Heurística | `0.5050 ± 0.0096` | `74.2433 ± 3.6357` | `0.5863 ± 0.0181` | `10.24 ± 0.43` |
| REINFORCE | `0.5105 ± 0.0629` | `0.5376 ± 3.2893` | `0.6971 ± 0.1189` | `32.92 ± 14.19` |

Interpretación del resultado disponible:

- REINFORCE supera a la heurística en éxito (`0.6971` frente a `0.5863`),
  pero no supera a la política aleatoria en fitness ni en éxito.
- La heurística obtiene la mayor recompensa bruta, aunque sus episodios son
  mucho más cortos.
- REINFORCE presenta mayor dispersión entre semillas, especialmente en
  longitud (`±14.19`), lo que indica menor estabilidad.
- La tabla corresponde al protocolo final regenerado después de los ajustes de
  agrupamiento y energía, con 5 semillas y diez episodios de evaluación
  por semilla.

## 6. Análisis cualitativo

Observaciones para el informe:

- el herbívoro alterna desplazamiento y consumo de alimento; con energía baja,
  `REST` puede ser útil, pero se penaliza cuando la energía ya es suficiente;
- el carnívoro busca coincidencias espaciales con herbívoros para ejecutar
  `HUNT`, por lo que la cacería depende de compartir exactamente la celda;
- la reproducción falla cuando no hay dos individuos elegibles en la misma
  celda o cuando la energía cae debajo del umbral;
- la exploración de REINFORCE se realiza muestreando desde la distribución
  softmax durante entrenamiento; la evaluación usa la política guardada sin
  exploración adicional;
- frente a la heurística, REINFORCE logra mayor éxito en el CSV disponible,
  pero todavía no demuestra superioridad global sobre ambos baselines.
- Frente a la literatura, el éxito de REINFORCE (`0.6971 ± 0.1189`) no es
  directamente comparable en escala con la recompensa de captura de Barton et
  al. (`13.70`) ni con el éxito de Xu y Dang (`99.9%`), porque emplean
  entornos, métricas y tareas diferentes. La comparación sí muestra que el
  simulador actual todavía no alcanza los niveles reportados por esos trabajos
  en sus respectivos escenarios; Pihlakas et al. aporta principalmente un
  marco conceptual de homeostasis y control de la extinción, no una cifra
  directamente transferible.

## 7. Reproducibilidad

El repositorio contiene semillas configurables, checkpoints por semilla,
pruebas automatizadas, el runner experimental y el estudio de sensibilidad.

Declaración de uso de IA:

> Se utilizó un asistente de IA como apoyo para revisar la estructura del
> código, proponer pruebas e implementar el runner del estudio de sensibilidad.
> El equipo definió el MDP, las recompensas y
> los hiperparámetros; ejecutó y verificó los experimentos, interpretó los
> resultados y es responsable del contenido final.

## 8. Módulo adicional: análisis de sensibilidad

Para el equipo de tres integrantes se eligió medir el efecto de la tasa de
aprendizaje sobre REINFORCE. Este módulo es un experimento adicional,
independiente de la evaluación principal de la Sección 5. Se comparan
`0.005`, `0.01` y `0.02`, manteniendo idénticos el entorno, `gamma`,
presupuesto de episodios y protocolo de evaluación. Cada tasa se ejecuta con
las semillas `1, 2, 3`, es decir, tres semillas por configuración.

El protocolo se ejecuta con:

```powershell
python run_sensitivity.py --output experiments/sensitivity --learning-rates 0.005 0.01 0.02 --epochs 10 --episodes 50 --steps-per-episode 50 --evaluation-episodes 10 --seeds 1 2 3
```

Los artefactos de este módulo están separados en `experiments/sensitivity/`.
El resultado consolidado es `experiments/sensitivity/sensitivity_summary.csv`.
La gráfica `sensitivity_comparison.png` mostrará la media y la desviación
estándar entre semillas para fitness, recompensa, éxito y longitud de episodio.

Resultados del módulo adicional (media ± desviación estándar entre las tres
semillas de cada configuración):

| Tasa de aprendizaje | Fitness | Recompensa | Éxito | Longitud |
|---:|---:|---:|---:|---:|
| `0.005` | `0.5184 ± 0.0882` | `-1.5560 ± 3.4705` | `0.7133 ± 0.1514` | `38.37 ± 2.76` |
| `0.010` | `0.4766 ± 0.0599` | `-1.4470 ± 2.4047` | `0.6343 ± 0.1160` | `26.73 ± 16.08` |
| `0.020` | `0.4766 ± 0.0599` | `-1.4470 ± 2.4047` | `0.6343 ± 0.1160` | `26.73 ± 16.08` |

Interpretación:

- `0.005` obtuvo el mejor fitness y la mayor tasa de éxito promedio.
- `0.005` también mostró una longitud de episodio más consistente
  (`±2.76`) que `0.01` y `0.02` (`±16.08`).
- `0.01` y `0.02` produjeron exactamente los mismos valores de evaluación
  por semilla en este presupuesto experimental. La verificación de los
  checkpoints confirma que sus pesos son distintos; la política neuronal se
  evalúa sin exploración, seleccionando la acción válida de mayor logit, por
  lo que el resultado es consistente con que ambos checkpoints eligieran las
  mismas acciones discretas en los episodios evaluados. Por tanto, aumentar la
  tasa de `0.01` a `0.02` no aportó una mejora observable.
- La recompensa media fue negativa en las tres configuraciones, por lo que
  el mejor criterio global para seleccionar la tasa es fitness junto con
  éxito y dispersión, no la recompensa aislada.

Conclusión del módulo: dentro del rango evaluado, `learning_rate=0.005` fue la
configuración más favorable y estable para este entorno. Esta conclusión se
limita a `500` episodios por especie, `gamma=0.99` y las semillas `1, 2, 3`;
no implica que sea óptima para cualquier presupuesto de entrenamiento.
