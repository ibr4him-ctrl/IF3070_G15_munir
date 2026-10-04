"""Simulated annealing for maximization using the shared valid-neighbor generator."""

import math
import random
import time
from copy import deepcopy
from dataclasses import dataclass

from munir.core.constraints import is_valid_state
from munir.core.models import State
from munir.core.neighbors import random_neighbor
from munir.core.objective import update_state_value


@dataclass(slots=True)
class SimulatedAnnealingResult:
    initial_state: State
    final_state: State
    last_state: State
    objective_history: list[float]
    best_objective_history: list[float]
    temperature_history: list[float]
    acceptance_probability_history: list[float | None]
    delta_history: list[float | None]
    accepted_history: list[bool | None]
    no_improvement_history: list[int]
    iterations: int
    non_improving_iterations: int
    stuck_events: int
    duration_seconds: float
    stop_reason: str


def simulated_annealing(
    initial_state: State,
    initial_temperature: float = 100.0,
    cooling_rate: float = 0.99,
    min_temperature: float = 0.01,
    max_iterations: int = 1000,
    seed: int | None = None,
) -> SimulatedAnnealingResult:
    """Return the best state, preserving the full trajectory of the current state.

    History index 0 describes the initial state, with no proposed move. Subsequent
    temperatures are the temperatures used for that iteration's acceptance test.
    Stuck events are starts of consecutive iterations without a new best value;
    this is a stagnation proxy, not a proof that all neighbors are worse.
    """
    if not math.isfinite(initial_temperature) or initial_temperature <= 0:
        raise ValueError("Initial temperature must be positive and finite")
    if not math.isfinite(cooling_rate) or not 0 < cooling_rate < 1:
        raise ValueError("Cooling rate must be finite and between 0 and 1")
    if not math.isfinite(min_temperature) or not 0 <= min_temperature < initial_temperature:
        raise ValueError("Minimum temperature must be nonnegative and below initial temperature")
    if (
        isinstance(max_iterations, bool)
        or not isinstance(max_iterations, int)
        or max_iterations <= 0
    ):
        raise ValueError("Maximum iterations must be a positive integer")
    if not is_valid_state(initial_state):
        raise ValueError("Initial state must be valid")

    started = time.perf_counter()
    rng = random.Random(seed)
    initial = deepcopy(initial_state)
    update_state_value(initial)
    current = deepcopy(initial)
    best = deepcopy(initial)
    temperature = initial_temperature
    objectives = [current.value]
    best_values = [best.value]
    temperatures = [temperature]
    probabilities: list[float | None] = [None]
    deltas: list[float | None] = [None]
    accepted_moves: list[bool | None] = [None]
    stagnation = [0]
    no_improvement = 0
    non_improving_iterations = 0
    stuck_events = 0
    stop_reason = "max_iterations"

    for _ in range(max_iterations):
        if not current.vehicles:
            stop_reason = "no_vehicles"
            break
        if temperature <= min_temperature:
            stop_reason = "min_temperature"
            break
        try:
            candidate = random_neighbor(current, rng)
        except RuntimeError:
            # The bounded sampler exhausted its attempts; not proof of local optimum.
            stop_reason = "neighbor_attempts_exhausted"
            break

        delta = candidate.value - current.value
        probability = 1.0 if delta >= 0 else math.exp(delta / temperature)
        accepted = delta >= 0 or rng.random() < probability
        if accepted:
            current = candidate
        if current.value > best.value:
            best = deepcopy(current)
            no_improvement = 0
        else:
            if no_improvement == 0:
                stuck_events += 1
            no_improvement += 1
            non_improving_iterations += 1

        objectives.append(current.value)
        best_values.append(best.value)
        temperatures.append(temperature)
        probabilities.append(probability)
        deltas.append(delta)
        accepted_moves.append(accepted)
        stagnation.append(no_improvement)
        temperature *= cooling_rate

    return SimulatedAnnealingResult(
        initial_state=initial,
        final_state=best,
        last_state=current,
        objective_history=objectives,
        best_objective_history=best_values,
        temperature_history=temperatures,
        acceptance_probability_history=probabilities,
        delta_history=deltas,
        accepted_history=accepted_moves,
        no_improvement_history=stagnation,
        iterations=len(objectives) - 1,
        non_improving_iterations=non_improving_iterations,
        stuck_events=stuck_events,
        duration_seconds=time.perf_counter() - started,
        stop_reason=stop_reason,
    )
