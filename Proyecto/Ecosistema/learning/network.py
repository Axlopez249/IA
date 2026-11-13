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

    def train_policy_gradient(
        self,
        observation: tuple[float, ...],
        action_index: int,
        return_value: float,
        learning_rate: float = 0.01,
    ) -> float:
        # Ajusta la politica para reforzar acciones con retornos positivos.
        # La perdida es -G_t log(pi(a_t|s_t)), la forma REINFORCE de policy gradient.
        if not 0 <= action_index < self.output_size:
            raise ValueError("El indice de la accion no es valido.")

        logits, cache = self.forward_with_cache(observation)
        probabilities = self.softmax(logits)
        # Un retorno alto aumenta la probabilidad de la accion; uno bajo la reduce.
        loss = -return_value * math.log(max(probabilities[action_index], 1e-12))
        output_gradient = [
            return_value * probability for probability in probabilities
        ]
        output_gradient[action_index] -= return_value

        output_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.output_size)
        ]
        output_bias_gradients = list(output_gradient)
        second_hidden_gradient = [0.0] * self.hidden_size

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

        second_pre_gradient = [
            second_hidden_gradient[index]
            * relu_derivative(cache["second_pre_activation"][index])
            for index in range(self.hidden_size)
        ]
        second_weight_gradients = [
            [0.0] * self.hidden_size for _ in range(self.hidden_size)
        ]
        first_hidden_gradient = [0.0] * self.hidden_size

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

        first_pre_gradient = [
            first_hidden_gradient[index]
            * relu_derivative(cache["first_pre_activation"][index])
            for index in range(self.hidden_size)
        ]
        first_weight_gradients = [
            [0.0] * self.input_size for _ in range(self.hidden_size)
        ]

        for first_index in range(self.hidden_size):
            for input_index in range(self.input_size):
                first_weight_gradients[first_index][input_index] = (
                    first_pre_gradient[first_index]
                    * cache["inputs"][input_index]
                )

        self.apply_gradients(
            first_weight_gradients,
            first_pre_gradient,
            second_weight_gradients,
            second_pre_gradient,
            output_weight_gradients,
            output_bias_gradients,
            learning_rate,
        )
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