# Red neuronal pequena implementada con listas y operaciones de Python puro.

from __future__ import annotations

import math
import random
from typing import Any


def relu(value: float) -> float:
    # Activa solo valores positivos y aporta no linealidad a la red.
    return max(0.0, value)


def relu_derivative(value: float) -> float:
    # Indica si una neurona ReLU deja pasar el gradiente.
    return 1.0 if value > 0.0 else 0.0


class NeuralNetwork:
    # Red multicapa sencilla para convertir observaciones en logits de acciones.

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 32,
        output_size: int = 6,
        seed: int = 0,
    ) -> None:
        # Inicializa pesos pequenos y reproducibles.
        generator = random.Random(seed)
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.first_weights = self.create_weights(input_size, hidden_size, generator)
        self.first_biases = [0.0] * hidden_size
        self.second_weights = self.create_weights(hidden_size, hidden_size, generator)
        self.second_biases = [0.0] * hidden_size
        self.output_weights = self.create_weights(hidden_size, output_size, generator)
        self.output_biases = [0.0] * output_size

    def to_dict(self) -> dict[str, Any]:
        """Serializa la arquitectura y los parámetros entrenados."""
        return {
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "first_weights": self.first_weights,
            "first_biases": self.first_biases,
            "second_weights": self.second_weights,
            "second_biases": self.second_biases,
            "output_weights": self.output_weights,
            "output_biases": self.output_biases,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NeuralNetwork":
        """Reconstruye una red previamente serializada."""
        required = (
            "input_size",
            "hidden_size",
            "output_size",
            "first_weights",
            "first_biases",
            "second_weights",
            "second_biases",
            "output_weights",
            "output_biases",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Faltan parametros de red: {', '.join(missing)}")

        network = cls(
            int(data["input_size"]),
            hidden_size=int(data["hidden_size"]),
            output_size=int(data["output_size"]),
        )
        network.first_weights = data["first_weights"]
        network.first_biases = data["first_biases"]
        network.second_weights = data["second_weights"]
        network.second_biases = data["second_biases"]
        network.output_weights = data["output_weights"]
        network.output_biases = data["output_biases"]
        network._validate_shapes()
        return network

    def _validate_shapes(self) -> None:
        if (
            len(self.first_weights) != self.hidden_size
            or any(len(row) != self.input_size for row in self.first_weights)
            or len(self.first_biases) != self.hidden_size
            or len(self.second_weights) != self.hidden_size
            or any(len(row) != self.hidden_size for row in self.second_weights)
            or len(self.second_biases) != self.hidden_size
            or len(self.output_weights) != self.output_size
            or any(len(row) != self.hidden_size for row in self.output_weights)
            or len(self.output_biases) != self.output_size
        ):
            raise ValueError("La forma de los parametros de red no es valida.")

    def create_weights(
        self,
        input_size: int,
        output_size: int,
        generator: random.Random,
    ) -> list[list[float]]:
        # Usa una inicializacion pequena para evitar activaciones enormes.
        scale = math.sqrt(2.0 / input_size)
        # Esto retorna una lista con la cantidad de filas igual a output_size y
        #  la cantidad de columnas igual a input_size.
        # Esto con el objetivo de acercarse a la representacion matricial de una capa densa.
        return [
            [generator.uniform(-scale, scale) for _ in range(input_size)]
            for _ in range(output_size)
        ]

    def calculate_layer(
        self,
        values: list[float],
        weights: list[list[float]],
        biases: list[float],
        activate: bool,
    ) -> list[float]:
        # Calcula una capa densa y aplica ReLU cuando corresponde.
        outputs = []
        for row, bias in zip(weights, biases):
            result = sum(weight * value for weight, value in zip(row, values)) + bias
            outputs.append(relu(result) if activate else result)
        return outputs

    def forward(self, observation: tuple[float, ...]) -> list[float]:
        # Propaga una observacion hasta producir un logit por accion.
        if len(observation) != self.input_size:
            raise ValueError(
                f"Se esperaban {self.input_size} valores, pero llegaron {len(observation)}"
            )
        hidden = self.calculate_layer(
            list(observation),
            self.first_weights,
            self.first_biases,
            activate=True,
        )
        hidden = self.calculate_layer(
            hidden,
            self.second_weights,
            self.second_biases,
            activate=True,
        )
        return self.calculate_layer(
            hidden,
            self.output_weights,
            self.output_biases,
            activate=False,
        )

    # Funcion para que los outputs de la red sean probabilidades y no logits, para que puedan ser interpretados como tal. La suma de todos da 1
    def softmax(self, logits: list[float]) -> list[float]:
        # Convierte logits en probabilidades sin desbordamientos numericos.
        maximum = max(logits)
        exponentials = [math.exp(logit - maximum) for logit in logits]
        total = sum(exponentials)
        return [value / total for value in exponentials]

    def forward_with_cache(
        self,
        observation: tuple[float, ...],
    ) -> tuple[list[float], dict[str, list[float]]]:
        # Guarda valores intermedios necesarios para retropropagar el error.
        if len(observation) != self.input_size:
            raise ValueError(
                f"Se esperaban {self.input_size} valores, pero llegaron {len(observation)}"
            )

        inputs = list(observation)
        first_pre_activation = self.calculate_layer(
            inputs,
            self.first_weights,
            self.first_biases,
            activate=False,
        )
        first_hidden = [relu(value) for value in first_pre_activation]
        second_pre_activation = self.calculate_layer(
            first_hidden,
            self.second_weights,
            self.second_biases,
            activate=False,
        )
        second_hidden = [relu(value) for value in second_pre_activation]
        logits = self.calculate_layer(
            second_hidden,
            self.output_weights,
            self.output_biases,
            activate=False,
        )
        cache = {
            "inputs": inputs,
            "first_pre_activation": first_pre_activation,
            "first_hidden": first_hidden,
            "second_pre_activation": second_pre_activation,
            "second_hidden": second_hidden,
        }
        return logits, cache

    def train_supervised(
        self,
        observation: tuple[float, ...],
        target_index: int,
        learning_rate: float = 0.01,
    ) -> float:
        # Ajusta los pesos para que la accion objetivo tenga mayor probabilidad.
        if not 0 <= target_index < self.output_size:
            raise ValueError("El indice de la accion objetivo no es valido.")

        logits, cache = self.forward_with_cache(observation)
        probabilities = self.softmax(logits)
        # Calcula la perdida de la red pasada de acuerdo a la observacion y la accion objetivo.
        loss = -math.log(max(probabilities[target_index], 1e-12))

        # La derivada de la entropia cruzada con softmax es probabilidad - objetivo.
        output_gradient = list(probabilities)
        # Se coloca negativo la desicion para que la red aprenda a aumentar la probabilidad de la accion objetivo.
        output_gradient[target_index] -= 1.0

        # Crea inicialmente gradientes de pesos y sesgos en cero para cada capa.
        output_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.output_size)
        ]
        output_bias_gradients = [0.0] * self.output_size
        second_hidden_gradient = [0.0] * self.hidden_size

        # 
        for output_index in range(self.output_size):
            output_bias_gradients[output_index] = output_gradient[output_index]
            # se asigna el gradiente de la capa de salida a la capa oculta anterior multiplicando por los pesos de salida.
            for hidden_index in range(self.hidden_size):
                # nuevos pesos de salida = pesos de salida - tasa de aprendizaje * gradiente de pesos de salida
                output_weight_gradients[output_index][hidden_index] = (
                    output_gradient[output_index] * cache["second_hidden"][hidden_index]
                )

                # Actualiza el gradiente de la capa oculta.
                # Para que influya en la salida de la siguiente
                second_hidden_gradient[hidden_index] += (
                    self.output_weights[output_index][hidden_index]
                    * output_gradient[output_index]
                )

        # Se utiliza la derivada de Relu para propagar el gradiente hacia la capa oculta anterior.
        second_pre_gradient = [
            second_hidden_gradient[index]
            * relu_derivative(cache["second_pre_activation"][index])
            for index in range(self.hidden_size)
        ]
        # Calcula los gradientes de los pesos y sesgos de la segunda capa oculta.
        second_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.hidden_size)
        ]
        # Calcula los gradientes de los sesgos de la segunda capa oculta.
        second_bias_gradients = list(second_pre_gradient)
        # Calcula el gradiente de la primera capa oculta.
        first_hidden_gradient = [0.0] * self.hidden_size

        # Propaga el gradiente hacia la primera capa oculta.
        for second_index in range(self.hidden_size):
            for first_index in range(self.hidden_size):

                # Calcula el gradiente de los pesos de la segunda capa oculta.
                second_weight_gradients[second_index][first_index] = (
                    second_pre_gradient[second_index]
                    * cache["first_hidden"][first_index]
                )
                # Actualiza el gradiente de la primera capa oculta multiplicando por los pesos de la segunda capa oculta.
                first_hidden_gradient[first_index] += (
                    self.second_weights[second_index][first_index]
                    * second_pre_gradient[second_index]
                )
        # Se utiliza la derivada de Relu para propagar el gradiente hacia la primera capa oculta.
        first_pre_gradient = [
            first_hidden_gradient[index]
            * relu_derivative(cache["first_pre_activation"][index])
            for index in range(self.hidden_size)
        ]
        # Calcula los gradientes de los pesos y sesgos de la primera capa oculta.
        first_weight_gradients = [
            [0.0] * self.input_size for _ in range(self.hidden_size)
        ]
        first_bias_gradients = list(first_pre_gradient)

        # Calcula los gradientes de los pesos de la primera capa oculta.
        for first_index in range(self.hidden_size):
            for input_index in range(self.input_size):
                first_weight_gradients[first_index][input_index] = (
                    first_pre_gradient[first_index]
                    * cache["inputs"][input_index]
                )

        # Actualiza todos los parametros despues de calcular todos los gradientes.
        self.apply_gradients(
            first_weight_gradients,
            first_bias_gradients,
            second_weight_gradients,
            second_bias_gradients,
            output_weight_gradients,
            output_bias_gradients,
            learning_rate,
        )
        return loss

    # Esta funcion recibe una decision tomada por la politica y el resultado
    # acumulado que produjo dentro del episodio. Con esa informacion calcula
    # como deben cambiar los pesos para aumentar las decisiones beneficiosas
    # y reducir las decisiones que llevaron a recompensas bajas.
    #
    # El metodo utiliza REINFORCE, cuyo objetivo es maximizar la probabilidad
    # de las acciones que obtuvieron buenos retornos en un estado determinado.
    def train_policy_gradient(
        self,
        observation: tuple[float, ...],
        action_index: int,
        return_value: float,
        learning_rate: float = 0.01,
        valid_action_indices: list[int] | None = None,
    ) -> float:
        # La accion debe existir dentro de la salida de la red. Esta primera
        # validacion evita actualizar una posicion de salida inexistente.
        if not 0 <= action_index < self.output_size:
            raise ValueError("El indice de la accion no es valido.")
        
        # La red transforma la observacion en un logit por accion.
        # El cache conserva las activaciones necesarias para calcular despues
        # los gradientes de cada capa durante la retropropagacion.
        logits, cache = self.forward_with_cache(observation)

        # Si no se especifica un filtro, todas las salidas de la red son validas.
        # Cuando se recibe una lista, solo esas acciones pueden participar en
        # la distribucion de probabilidad de la especie que se esta entrenando.
        valid_indices = (
            list(range(self.output_size))
            if valid_action_indices is None
            else valid_action_indices
        )

        # No se puede entrenar una politica sin acciones disponibles.
        # Tambien se verifica que cada indice apunte a una salida real de la red.
        if not valid_indices or any(
            not 0 <= index < self.output_size for index in valid_indices
        ):
            raise ValueError("Los indices de acciones validas no son correctos.")

        # La accion que se esta reforzando debe pertenecer al conjunto permitido.
        # Por ejemplo, un herbivoro no puede aprender una accion de caceria.
        if action_index not in valid_indices:
            raise ValueError("La accion elegida debe ser valida para la politica.")

        # Se calcula softmax solo sobre las acciones validas. De esta forma,
        # las acciones imposibles no reciben probabilidad ni interfieren en
        # la actualizacion de la politica.
        valid_logits = [logits[index] for index in valid_indices]
        valid_probabilities = self.softmax(valid_logits)

        # Se reconstruye el vector completo para conservar la posicion original
        # de cada accion. Las acciones invalidas permanecen con probabilidad cero.
        probabilities = [0.0] * self.output_size
        for index, probability in zip(valid_indices, valid_probabilities):
            probabilities[index] = probability

        # La perdida de REINFORCE es:
        #
        #     perdida = -G_t * log(pi(a_t | s_t))
        #
        # Si el retorno es positivo, el descenso de gradiente aumenta la
        # probabilidad de la accion tomada. Si es negativo, la reduce.
        loss = -return_value * math.log(max(probabilities[action_index], 1e-12))

        # Para softmax, el gradiente de cada salida comienza siendo su
        # probabilidad multiplicada por el retorno. Luego se corrige la salida
        # correspondiente a la accion que realmente se ejecuto.
        output_gradient = [
            return_value * probability for probability in probabilities
        ]
        output_gradient[action_index] -= return_value

        # Se preparan las matrices de gradientes de la capa de salida.
        # Cada salida representa una accion posible de la politica.
        output_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.output_size)
        ]
        output_bias_gradients = list(output_gradient)
        second_hidden_gradient = [0.0] * self.hidden_size

        # El gradiente de cada peso de salida depende del gradiente de la accion
        # y de la activacion que llego desde la segunda capa oculta.
        # Al mismo tiempo se propaga el error hacia esa capa anterior.
        for output_index in range(self.output_size):
            for hidden_index in range(self.hidden_size):
                output_weight_gradients[output_index][hidden_index] = (
                    output_gradient[output_index]
                    * cache["second_hidden"][hidden_index]
                )
                second_hidden_gradient[hidden_index] += (
                    self.output_weights[output_index][hidden_index]
                    * output_gradient[output_index]
                )

        # Se atraviesa la funcion ReLU de la segunda capa. Solo las neuronas
        # activas pueden continuar transmitiendo el gradiente.
        second_pre_gradient = [
            second_hidden_gradient[index]
            * relu_derivative(cache["second_pre_activation"][index])
            for index in range(self.hidden_size)
        ]

        # Se calculan los gradientes de los pesos de la segunda capa oculta y
        # se prepara la propagacion del error hacia la primera capa oculta.
        second_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.hidden_size)
        ]
        first_hidden_gradient = [0.0] * self.hidden_size

        # Cada conexion de esta capa se ajusta usando el gradiente recibido y
        # la activacion producida por la capa oculta anterior.
        for second_index in range(self.hidden_size):
            for first_index in range(self.hidden_size):
                second_weight_gradients[second_index][first_index] = (
                    second_pre_gradient[second_index]
                    * cache["first_hidden"][first_index]
                )
                first_hidden_gradient[first_index] += (
                    self.second_weights[second_index][first_index]
                    * second_pre_gradient[second_index]
                )

        # Se continua retrocediendo por la primera funcion ReLU para obtener
        # el gradiente que corresponde a la primera capa oculta.
        first_pre_gradient = [
            first_hidden_gradient[index]
            * relu_derivative(cache["first_pre_activation"][index])
            for index in range(self.hidden_size)
        ]

        # Se calculan los gradientes de las conexiones entre la observacion
        # original y la primera capa oculta de la red.
        first_weight_gradients = [
            [0.0] * self.input_size for _ in range(self.hidden_size)
        ]

        for first_index in range(self.hidden_size):
            for input_index in range(self.input_size):
                first_weight_gradients[first_index][input_index] = (
                    first_pre_gradient[first_index]
                    * cache["inputs"][input_index]
                )

        # Todas las capas se actualizan juntas para que la red conserve una
        # sola actualizacion coherente para esta observacion y su retorno.
        self.apply_gradients(
            first_weight_gradients,
            first_pre_gradient,
            second_weight_gradients,
            second_pre_gradient,
            output_weight_gradients,
            output_bias_gradients,
            learning_rate,
        )

        # Se devuelve la perdida para registrar el progreso del episodio y
        # comparar el comportamiento del entrenamiento entre iteraciones.
        return loss

    def apply_gradients(
        self,
        first_weight_gradients: list[list[float]],
        first_bias_gradients: list[float],
        second_weight_gradients: list[list[float]],
        second_bias_gradients: list[float],
        output_weight_gradients: list[list[float]],
        output_bias_gradients: list[float],
        learning_rate: float,
    ) -> None:
        # Aplica descenso de gradiente a cada peso y sesgo de la red.
        for row_index in range(len(self.first_weights)):
            for column_index in range(len(self.first_weights[row_index])):
                # Actualiza los pesos de la primera capa oculta.
                self.first_weights[row_index][column_index] -= (
                    learning_rate * first_weight_gradients[row_index][column_index]
                )
            # Actualiza los sesgos de la primera capa oculta.
            self.first_biases[row_index] -= learning_rate * first_bias_gradients[row_index]

        for row_index in range(len(self.second_weights)):
            for column_index in range(len(self.second_weights[row_index])):
                # Actualiza los pesos de la segunda capa oculta.
                self.second_weights[row_index][column_index] -= (
                    learning_rate * second_weight_gradients[row_index][column_index]
                )
            # Actualiza los sesgos de la segunda capa oculta.
            self.second_biases[row_index] -= learning_rate * second_bias_gradients[row_index]

        for row_index in range(len(self.output_weights)):
            for column_index in range(len(self.output_weights[row_index])):
                # Actualiza los pesos de la capa de salida.
                self.output_weights[row_index][column_index] -= (
                    learning_rate * output_weight_gradients[row_index][column_index]
                )
            # Actualiza los sesgos de la capa de salida.
            self.output_biases[row_index] -= learning_rate * output_bias_gradients[row_index]