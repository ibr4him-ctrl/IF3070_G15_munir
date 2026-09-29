import random
from copy import deepcopy
from dataclasses import dataclass

from munir.core.constraints import is_valid_state
from munir.core.initial_state import create_random_initial_state
from munir.core.models import State
from munir.core.neighbors import random_neighbor
from munir.core.objective import update_state_value


@dataclass(slots=True)
class GeneticAlgorithmResult:
    initial_best_state: State
    best_state: State
    maximum_history: list[float]
    average_history: list[float]
    generations: int
    population_size: int


def _record_population(population: list[State]) -> tuple[float, float]:
    values = [state.value for state in population]
    return max(values), sum(values) / len(values)


def _tournament_selection(
    population: list[State],
    rng: random.Random,
    tournament_size: int,
) -> State:
    candidates = rng.sample(population, min(tournament_size, len(population)))
    return max(candidates, key=lambda state: state.value)


def _repair_state(state: State) -> State:
    candidate = deepcopy(state)
    placements = {
        vehicle.id: (vehicle.x, vehicle.y, vehicle.orientation)
        for vehicle in candidate.vehicles
    }

    for vehicle in candidate.vehicles:
        vehicle.x = None
        vehicle.y = None

    for vehicle in candidate.vehicles:
        x, y, orientation = placements[vehicle.id]
        vehicle.orientation = orientation
        vehicle.x = x
        vehicle.y = y

        if not is_valid_state(candidate):
            vehicle.x = None
            vehicle.y = None

    update_state_value(candidate)
    return candidate


def _crossover(first: State, second: State, rng: random.Random) -> State:
    child = deepcopy(first)
    second_vehicles = {vehicle.id: vehicle for vehicle in second.vehicles}

    for vehicle in child.vehicles:
        source = rng.choice((vehicle, second_vehicles[vehicle.id]))
        vehicle.x = source.x
        vehicle.y = source.y
        vehicle.orientation = source.orientation

    return _repair_state(child)


def _mutate(state: State, rng: random.Random) -> State:
    try:
        return random_neighbor(state, rng)
    except (RuntimeError, ValueError):
        return deepcopy(state)


def genetic_algorithm(
    problem: State,
    population_size: int = 50,
    generations: int = 100,
    mutation_rate: float = 0.1,
    elitism_count: int = 1,
    tournament_size: int = 3,
    seed: int | None = None,
) -> GeneticAlgorithmResult:
    if population_size < 2:
        raise ValueError("Population size must be at least 2")
    if generations <= 0:
        raise ValueError("Generations must be positive")
    if not 0 <= mutation_rate <= 1:
        raise ValueError("Mutation rate must be between 0 and 1")
    if not 0 <= elitism_count < population_size:
        raise ValueError("Elitism count must be smaller than population size")
    if tournament_size <= 0:
        raise ValueError("Tournament size must be positive")

    rng = random.Random(seed)
    population = [
        create_random_initial_state(problem, rng.randrange(2**32))
        for _ in range(population_size)
    ]

    initial_best = deepcopy(max(population, key=lambda state: state.value))
    best = deepcopy(initial_best)
    maximum, average = _record_population(population)
    maximum_history = [maximum]
    average_history = [average]

    for _ in range(generations):
        population.sort(key=lambda state: state.value, reverse=True)
        next_population = [deepcopy(state) for state in population[:elitism_count]]

        while len(next_population) < population_size:
            first = _tournament_selection(population, rng, tournament_size)
            second = _tournament_selection(population, rng, tournament_size)
            child = _crossover(first, second, rng)

            if rng.random() < mutation_rate:
                child = _mutate(child, rng)

            next_population.append(child)

        population = next_population
        generation_best = max(population, key=lambda state: state.value)
        if generation_best.value > best.value:
            best = deepcopy(generation_best)

        maximum, average = _record_population(population)
        maximum_history.append(maximum)
        average_history.append(average)

    return GeneticAlgorithmResult(
        initial_best_state=initial_best,
        best_state=best,
        maximum_history=maximum_history,
        average_history=average_history,
        generations=generations,
        population_size=population_size,
    )
