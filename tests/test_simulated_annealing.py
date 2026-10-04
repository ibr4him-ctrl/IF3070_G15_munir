from copy import deepcopy
from dataclasses import asdict
from importlib import import_module

import pytest

from munir.core.constraints import is_valid_state
from munir.core.initial_state import create_random_initial_state
from munir.core.models import Ship, State, Vehicle


def anneal(*args, **kwargs):
    return import_module("munir.algorithms.simulated_annealing").simulated_annealing(
        *args, **kwargs
    )


def problem():
    return State(
        Ship(4, 4, 9),
        [
            Vehicle("A", 2, 2, 60, 4, 1),
            Vehicle("B", 1, 3, 40, 3, 2),
            Vehicle("C", 2, 3, 75, 5, 1),
        ],
    )


def test_sa_valid_best_result_and_does_not_mutate_input():
    initial = create_random_initial_state(problem(), 10)
    before = deepcopy(initial)
    result = anneal(initial, max_iterations=100, seed=42)
    assert initial == before
    assert is_valid_state(result.final_state)
    assert is_valid_state(result.last_state)
    assert result.final_state.value == max(result.objective_history)
    assert result.final_state.value >= result.initial_state.value
    assert result.best_objective_history == sorted(result.best_objective_history)
    assert len(result.objective_history) == result.iterations + 1
    assert result.duration_seconds >= 0


def test_seed_reproduces_states_and_every_search_metric():
    initial = create_random_initial_state(problem(), 15)
    first = asdict(anneal(initial, max_iterations=80, seed=5))
    second = asdict(anneal(initial, max_iterations=80, seed=5))
    first.pop("duration_seconds")
    second.pop("duration_seconds")
    assert first == second


def test_acceptance_formula_and_best_survives_accepted_downhill_move():
    # One cell means every move is unloading/loading or an equal-valued rotation.
    initial = State(Ship(1, 1, 1), [Vehicle("A", 1, 1, 10, 1, 0, x=0, y=0)])
    result = anneal(
        initial,
        initial_temperature=100,
        cooling_rate=0.99,
        min_temperature=0.01,
        max_iterations=100,
        seed=12,
    )
    downhill = [
        i for i, delta in enumerate(result.delta_history) if delta is not None and delta < 0
    ]
    assert downhill
    assert any(result.accepted_history[i] for i in downhill)
    assert min(result.objective_history) == 0
    assert result.final_state.value == 10
    for i in downhill:
        import math

        assert result.acceptance_probability_history[i] == pytest.approx(
            math.exp(-10 / result.temperature_history[i])
        )
    for i, delta in enumerate(result.delta_history):
        if delta is not None and delta >= 0:
            assert result.acceptance_probability_history[i] == 1
            assert result.accepted_history[i]


def test_cooling_stops_at_minimum_and_histories_align():
    result = anneal(
        create_random_initial_state(problem(), 1),
        initial_temperature=8,
        cooling_rate=0.5,
        min_temperature=1,
        max_iterations=100,
        seed=2,
    )
    assert result.iterations == 3
    assert result.temperature_history == [8, 8, 4, 2]
    assert result.stop_reason == "min_temperature"
    assert result.acceptance_probability_history[0] is None
    for history in [
        result.temperature_history,
        result.acceptance_probability_history,
        result.no_improvement_history,
        result.best_objective_history,
        result.delta_history,
        result.accepted_history,
    ]:
        assert len(history) == 4


def test_stagnation_counts_best_without_claiming_local_optimum():
    initial = State(Ship(1, 1, 1), [Vehicle("A", 1, 1, 10, 1, 0, x=0, y=0)])
    result = anneal(initial, max_iterations=10, seed=3)
    assert result.no_improvement_history == list(range(11))
    assert result.non_improving_iterations == 10
    assert result.stuck_events == 1


@pytest.mark.parametrize(
    "parameters",
    [
        {"initial_temperature": 0},
        {"initial_temperature": float("inf")},
        {"cooling_rate": 0},
        {"cooling_rate": 1},
        {"cooling_rate": float("nan")},
        {"min_temperature": -1},
        {"min_temperature": 200},
        {"max_iterations": 0},
        {"max_iterations": 1.5},
    ],
)
def test_invalid_parameters_rejected(parameters):
    with pytest.raises(ValueError):
        anneal(problem(), **parameters)


def test_invalid_initial_state_rejected():
    initial = State(Ship(1, 1, 1), [Vehicle("A", 2, 2, 10, 1, 0, x=0, y=0)])
    with pytest.raises(ValueError, match="valid"):
        anneal(initial)


def test_empty_problem_returns_valid_state_without_iterations():
    result = anneal(State(Ship(1, 1, 1)), seed=0)
    assert result.iterations == 0
    assert result.objective_history == [0]
    assert result.final_state.vehicles == []
    assert result.stop_reason == "no_vehicles"
