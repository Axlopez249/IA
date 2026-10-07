import random
import copy
import time

class EvolutionaryAgent:

    def __init__(self, engine, seed, time_limit):

        # Motor del juego
        self.engine = engine

        # Semilla para reproducibilidad
        self.seed = seed
        random.seed(seed)

        # Límite de tiempo
        self.time_limit = time_limit
        self.tiempo_inicio = time.perf_counter()
        self.limite_tiempo_seguro = max(
            0.0,
            time_limit - max(0.001, time_limit * 0.02),
        )
        self.tiempo_transcurrido = 0.0

        # Parámetros del algoritmo evolutivo
        self.population_size = 100
        self.selection_size = 20
        self.elite_size = 5
        self.mutation_rate = 0.10

        # Parámetros del fitness
        self.W_FUSIONS = 100
        self.W_MAX_TILE = 10
        self.W_FREE_CELLS = 5

        # Plan/acción que se irá utilizando
        self.plan = []

        # Índice de la ficha actual
        self.index = 0

        # Mejor individuo encontrado
        self.best_individual = None

        # Medida de esfuerzo requerida
        self.evaluaciones_aptitud = 0

    # ==========================================================
    # INTERFAZ DEL AGENTE
    # ==========================================================

    def get_action(self, state, valid_actions):
        """
        Recibe el estado actual y devuelve una única acción
        para la siguiente ficha.
        """

        if self.plan:
            return self.plan.pop(0)

        if not valid_actions or self._tiempo_agotado():
            return None

        self.plan = self.evolve(state)

        if self.plan:
            return self.plan.pop(0)

        return None
    

    # ==========================================================
    # PROCESO EVOLUTIVO
    # ==========================================================

    def evolve(self, state):
        """
        Ejecuta el proceso evolutivo y devuelve
        el mejor individuo encontrado.
        """
        # Se crea la población inicial de individuos tomando como punto de inicio el estado actual del juego.
        population = self.create_population(state)

        while population and not self._tiempo_agotado():
            # Se evalúa la población para calcular el fitness de cada individuo.
            evaluated_population = self.evaluate_population(population)
            if not evaluated_population:
                break

            # Se seleccionan los mejores individuos para la siguiente generación.
            selected = self.select(evaluated_population)

            # Se aplica tanto el operador de crossover como el de mutación para generar nuevos individuos a partir de los seleccionados.
            population = self.create_offspring(selected, state)

        self.tiempo_transcurrido = time.perf_counter() - self.tiempo_inicio

        if self.best_individual is None:
            return []

        # Se devuelve el plan de acciones del mejor individuo encontrado.
        return self.best_individual[0][5]

    # ==========================================================
    # POBLACIÓN
    # ==========================================================

    # Funcino para crear la población inicial de individuos tomando como punto de inicio el estado actual del juego. 
    # Cada individuo es una lista de acciones (genes) que representan un plan para las fichas restantes.
    def create_population(self, state):
        """
        Crea la población inicial de individuos.
        """
        population = []

        fichas_restantes = state["m"] - state["next_piece_index"]

        for _ in range(self.population_size):
            # Cada gen representa una proporción de la lista de celdas vacías.
            genes = [random.random() for _ in range(fichas_restantes)]
            population.append(self.simulate_individual(state, genes))

        return population

    def create_random_position (self, state):
        """
        Crea una posición aleatoria para la ficha actual
        en el estado dado.
        """
        valid_actions = self.engine.get_valid_actions(state)
        return random.choice(valid_actions)
    # ==========================================================
    # SIMULACIÓN
    # ==========================================================

    def simulate_individual(self, state, genes):
        """
        Simula todas las acciones de un individuo
        utilizando el motor del juego.
        """
        state_copy = copy.deepcopy(state)
        actions = []
        fusion = 0

        for gene in genes:
            valid_actions = self.engine.get_valid_actions(state_copy)
            if not valid_actions or self._tiempo_agotado():
                break

            # El gen se convierte en un índice de una celda vacía para evitar jugadas ilegales.
            indice = min(int(gene * len(valid_actions)), len(valid_actions) - 1)
            action = valid_actions[indice]
            occupied_before = self.engine.get_occupied_cells(state_copy)
            state_copy = self.engine.update_state(state_copy, action)
            occupied_after = self.engine.get_occupied_cells(state_copy)

            actions.append(action)
            if occupied_before == occupied_after:
                fusion += 1

        free_cells = state_copy["n"] ** 2 - self.engine.get_occupied_cells(state_copy)
        max_tile = self.engine.get_max_piece_value(state_copy)

        # Se agrega el plan de acciones al final para conservar la estructura de la tupla actual.
        return (list(genes), state_copy, fusion, max_tile, free_cells, actions)

    # ==========================================================
    # EVALUACIÓN
    # ==========================================================

    def evaluate_population(self, population):
        """
        Calcula el fitness de todos los individuos
        de la población.
        """
        evaluated_population = []
        for candidate in population:
            if self._tiempo_agotado() and evaluated_population:
                break

            # se saca cada individuo de la población y se calcula su fitness a partir del estado final de su simulación.
            fitness = self.calculate_fitness(candidate)
            self.evaluaciones_aptitud += 1
            # se agrega el individuo y su fitness a la lista de población evaluada.
            evaluated_population.append((candidate, fitness))
        return evaluated_population

    def calculate_fitness(self, individual):
        """
        Calcula qué tan bueno fue un individuo
        a partir del estado final de su simulación.
        """
        # Se prioriza consumir fichas y luego dejar la mayor cantidad de celdas libres.
        fichas_colocadas = len(individual[5])
        fitness = (fichas_colocadas * 1000000) + individual[4]
        return fitness
        

    # ==========================================================
    # SELECCIÓN
    # ==========================================================

    def select(self, population):
        """
        Selecciona los mejores individuos que podrán
        reproducirse.
        """
        if not population:
            raise ValueError("No se puede seleccionar una población vacía.")

        # La población evaluada contiene pares: (individuo, fitness).
        # esta seccion ordena la población evaluada de mayor a menor fitness y 
        # selecciona los mejores individuos para la siguiente generación.
        ordered_population = sorted(
            population,
            key=lambda evaluated: evaluated[1],
            reverse=True,
        )

        # Se obtiene el mejor individuo de la población ordenada y se compara con el mejor individuo encontrado 
        # hasta ahora. Si el nuevo individuo es mejor, se actualiza el mejor individuo.
        current_best = self.get_best(ordered_population)
        # Condicional
        if self.best_individual is None:
            self.best_individual = current_best
        elif current_best[1] > self.best_individual[1]:
            self.best_individual = current_best

        # El primer elemento siempre es el mejor y queda incluido en la selección.
        return ordered_population[:self.selection_size]

    def get_best(self, population):
        """
        Devuelve el mejor individuo de una población.
        """
        if not population:
            raise ValueError("No se puede obtener el mejor de una población vacía.")

        best_evaluated = max(population, key=lambda evaluated: evaluated[1])
        return best_evaluated

    # ==========================================================
    # REPRODUCCIÓN
    # ==========================================================

    def create_offspring(self, selected, state):
        """
        Crea una nueva población mediante selección de padres,
        crossover y mutación.
        """
        offspring = []

        i = 0

        # Se hace el ciclo para generar descendencia hasta que se alcance el tamaño de población deseado.
        while len(offspring) < self.population_size:

            parent1 = selected[i % len(selected)][0]
            parent2 = selected[(i + 1) % len(selected)][0]

            # Se realiza el crossover entre los padres para generar un hijo.
            child = self.crossover(parent1, parent2, state)

            # Se aplica la mutación al hijo generado.
            mutated_child = self.mutate(child, state)

            # Se agrega el hijo mutado a la descendencia.
            offspring.append(mutated_child)

            i += 2
        return offspring

    def crossover(self, parent1, parent2, state):
        """
        Combina dos individuos para producir un hijo.
        """
        genes_padre_1 = parent1[0]
        genes_padre_2 = parent2[0]

        if not genes_padre_1:
            return self.simulate_individual(state, genes_padre_2)

        if not genes_padre_2:
            return self.simulate_individual(state, genes_padre_1)

        # Se carga la mitad de los genes del primer padre y la otra mitad del segundo padre.
        punto_cruce = random.randint(1, min(len(genes_padre_1), len(genes_padre_2)))
        genes_hijo = (
            genes_padre_1[:punto_cruce]
            + genes_padre_2[punto_cruce:]
        )

        return self.simulate_individual(state, genes_hijo)

    def mutate(self, individual, state):
        """
        Aplica mutaciones a un individuo.
        """
        # Se crea una copia de los genes para no modificar el individuo original.
        genes = list(individual[0])

        if not genes:
            return individual

        # Se reemplaza aleatoriamente un gen por otro valor entre 0.0 y 1.0.
        if random.random() < self.mutation_rate:
            random_index = random.randint(0, len(genes) - 1)
            genes[random_index] = random.random()

        return self.simulate_individual(state, genes)

    

    # ==========================================================
    # UTILIDADES
    # ==========================================================

    def _tiempo_agotado(self):
        """Determina si se alcanzó el límite global de tiempo del agente."""
        return time.perf_counter() - self.tiempo_inicio >= self.limite_tiempo_seguro

    def update_individual(self, state, index, position):
        """
        Mueve la pieza indicada por index a una nueva posición
        sin modificar next_piece_index.
        """
        state_copy = copy.deepcopy(state)

        # Obtener la pieza que corresponde al gen que se está modificando
        piece = state_copy["pieces"][index]


        # Colocar la pieza y aplicar las reglas de fusión
        self.engine.update_board(
            position[0],
            position[1],
            piece,
            state_copy
        )

        return state_copy