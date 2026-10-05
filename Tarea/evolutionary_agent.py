import random
import copy

class EvolutionaryAgent:

    def __init__(self, engine, seed, time_limit):

        # Motor del juego
        self.engine = engine

        # Semilla para reproducibilidad
        self.seed = seed
        random.seed(seed)

        # Límite de tiempo
        self.time_limit = time_limit

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

    # ==========================================================
    # INTERFAZ DEL AGENTE
    # ==========================================================

    def get_action(self, state):
        """
        Recibe el estado actual y devuelve una única acción
        para la siguiente ficha.
        """

        return self.evolve(state)
    

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

        # Se evalúa la población inicial para calcular el fitness de cada individuo.
        population = self.evaluate_population(population)

        # Se seleccionan los mejores individuos para la siguiente generación.
        selected = self.select(population)

        # Se aplica tanto el operador de crossover como el de mutación para generar nuevos individuos a partir de los seleccionados.
        offspring = self.create_offspring(selected, state)

        # Se devuelve el mejor individuo encontrado.
        return self.get_best_individual(offspring)

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

        for _ in range(self.population_size):
            individual = []
            state_copy = copy.deepcopy(state)
            fusion = 0
            
            for _ in range(state_copy["m"] - state_copy["next_piece_index"]):
                #Verificar si se tienen celdas libres para colocar la ficha actual, si no hay celdas libres, se rompe el bucle y se termina de crear el individuo.
                valid_actions = self.engine.get_valid_actions(state_copy)
                if not valid_actions:
                    break
                
                # Se obtiene el tamaño del tablero antes de aplicar la acción para verificar si se produce una fusión.
                occupied_before = self.engine.get_occupied_cells(state_copy)
                
                # Se crea una acción aleatoria para la ficha actual y se agrega al individuo.
                action = self.create_random_position(state_copy) 
                individual.append(action)

                # Se actualiza el estado del juego con la acción seleccionada para simular el efecto de la acción en el juego.
                # Verificando de una vez si la acción generada es válida para el estado actual del juego.
                state_copy = self.engine.update_state(state_copy, action)
                occupied_after = self.engine.get_occupied_cells(state_copy)

                # Se verifica si la acción generada produjo una fusión en el juego y se actualiza el contador de fusiones.
                if occupied_before == occupied_after:
                    fusion += 1


            # Sacar celdas libres y max tile
            free_cells = (state_copy["n"] ** 2 - self.engine.get_occupied_cells(state_copy)
)           # Sacar el valor máximo de ficha en el estado final del individuo.
            max_tile = self.engine.get_max_piece_value(state_copy)

            # Se agrega el individuo a la población junto con su estado final, número de fusiones,
            # valor máximo de ficha y número de celdas libres.
            population.append((individual,state_copy,fusion,max_tile,free_cells))

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
        pass

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
            # se saca cada individuo de la población y se calcula su fitness a partir del estado final de su simulación.
            fitness = self.calculate_fitness(candidate)
            # se agrega el individuo y su fitness a la lista de población evaluada.
            evaluated_population.append((candidate, fitness))
        return evaluated_population

    def calculate_fitness(self, individual):
        """
        Calcula qué tan bueno fue un individuo
        a partir del estado final de su simulación.
        """
        fitness = (self.W_FUSIONS * individual[2]) + (self.W_MAX_TILE * individual[3]) + (self.W_FREE_CELLS * individual[4])
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

            parent1 = selected[i % len(selected)]
            parent2 = selected[(i + 1) % len(selected)]

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
        individio_nuevo = []

        # Con este for se carga la mitad de los genes del primer padre
        posiciones = []
        state_copy = copy.deepcopy(state)
        fusion = 0
        for i in range(0, len(parent1[0]) // 2):
            # Consultar tamaño
            occupied_before = self.engine.get_occupied_cells(state_copy)

            posiciones.append(parent1[0][i])
            state_copy = self.engine.update_state(state_copy, parent1[0][i])

            occupied_after = self.engine.get_occupied_cells(state_copy)
            if occupied_before == occupied_after:
                fusion += 1


        # Con este for se carga la otra mitad de los genes del segundo padre
        for i in range(len(parent2[0]) // 2, len(parent2[0])):

            valid_actions = self.engine.get_valid_actions(state_copy)

            if parent2[0][i] in valid_actions:
                occupied_before = self.engine.get_occupied_cells(state_copy)

                posiciones.append(parent2[0][i])
                state_copy = self.engine.update_state(state_copy, parent2[0][i])

                occupied_after = self.engine.get_occupied_cells(state_copy)
                if occupied_before == occupied_after:
                    fusion += 1
            else:
                # Si la acción del segundo padre ya está en el hijo, se genera una acción aleatoria para evitar duplicados.
                action = self.create_random_position(state_copy)
                posiciones.append(action)
                state_copy = self.engine.update_state(state_copy, action)

        # Sacar celdas libres y max tile
        free_cells = (state_copy["n"] ** 2 - self.engine.get_occupied_cells(state_copy))
        # Sacar el valor máximo de ficha en el estado final del individuo.
        max_tile = self.engine.get_max_piece_value(state_copy)

        individio_nuevo = (posiciones, state_copy, fusion, max_tile, free_cells)
        
        return (individio_nuevo)

    def mutate(self, individual, state):
        """
        Aplica mutaciones a un individuo.
        """
        # Implementar lógica de mutación
        # Se crea una copia del individuo para no modificar el original.
        state_copy = copy.deepcopy(individual[1])

        random_position = self.create_random_position(state_copy)
        random_index = random.randint(0, len(individual[0]) - 1)
        fusion = individual[2]

        occupied_before = self.engine.get_occupied_cells(state_copy)
        # Reemplazar el gen en la posición aleatoria con la posición aleatoria
        state_copy = self.update_individual(state_copy, random_index, random_position)

        occupied_after = self.engine.get_occupied_cells(state_copy)
        if occupied_before == occupied_after:
            fusion += 1

        # Sacar celdas libres y max tile
        free_cells = (state_copy["n"] ** 2 - self.engine.get_occupied_cells(state_copy))
        # Sacar el valor máximo de ficha en el estado final del individuo.
        max_tile = self.engine.get_max_piece_value(state_copy)

        # Se cambia el gen en la posición aleatoria con la nueva posición aleatoria y se actualiza el estado del individuo.
        individual[0][random_index] = random_position

        return (individual[0], state_copy, fusion, max_tile, free_cells)

    

    # ==========================================================
    # UTILIDADES
    # ==========================================================

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
