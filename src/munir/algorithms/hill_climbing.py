import random
from copy import deepcopy
from dataclasses import dataclass

from munir.core.models import State
from munir.core.neighbors import random_neighbor
from munir.core.objective import update_state_value


@dataclass(slots=True)
class HillClimbingResult:
    initial_state: State
    final_state: State
    objective_history: list[float]
    iterations: int


def stochastic_hill_climbing(
    initial_state: State,
    max_iterations: int = 1000,
    max_no_improvement: int = 100,
    seed: int | None = None,
) -> HillClimbingResult:
    if max_iterations <= 0:
        raise ValueError("Maximum iterations must be positive")
    if max_no_improvement <= 0:
        raise ValueError("Maximum no improvement must be positive")

    rng = random.Random(seed)
    initial = deepcopy(initial_state)
    current = deepcopy(initial_state)
    update_state_value(initial)
    update_state_value(current)

    history = [current.value]
    no_improvement = 0
    iterations = 0

    for iteration in range(1, max_iterations + 1):
        try:
            neighbor = random_neighbor(current, rng)
        except RuntimeError:
            break

        if neighbor.value > current.value:
            current = neighbor
            no_improvement = 0
        else:
            no_improvement += 1

        history.append(current.value)
        iterations = iteration

        if no_improvement >= max_no_improvement:
            break

    return HillClimbingResult(
        initial_state=initial,
        final_state=current,
        objective_history=history,
        iterations=iterations,
    )
