from pathlib import Path

from munir.core.constraints import is_valid_state
from munir.core.initial_state import create_random_initial_state
from munir.io.json_loader import load_problem


PROBLEM_PATH = Path(__file__).resolve().parents[1] / "configs/problem.reference16.json"
EXPECTED_VEHICLES = [
    ("V01", 2, 3, 80, 5, 1),
    ("V02", 2, 4, 115, 7, 2),
    ("V03", 3, 3, 145, 9, 3),
    ("V04", 2, 2, 65, 4, 4),
    ("V05", 3, 4, 180, 12, 5),
    ("V06", 1, 3, 48, 3, 1),
    ("V07", 2, 3, 95, 6, 2),
    ("V08", 2, 2, 72, 5, 3),
    ("V09", 3, 2, 108, 7, 4),
    ("V10", 1, 4, 62, 4, 5),
    ("V11", 3, 3, 160, 11, 1),
    ("V12", 2, 4, 135, 8, 2),
    ("V13", 2, 2, 84, 6, 3),
    ("V14", 1, 2, 36, 2, 4),
    ("V15", 3, 4, 195, 13, 5),
    ("V16", 2, 3, 100, 7, 1),
]


def test_reference16_loader_reads_exact_benchmark_attributes() -> None:
    problem = load_problem(PROBLEM_PATH)

    assert (problem.ship.width, problem.ship.length, problem.ship.max_capacity) == (8, 12, 55)
    assert len(problem.vehicles) == 16
    assert [
        (
            vehicle.id,
            vehicle.width,
            vehicle.length,
            vehicle.shipping_fee,
            vehicle.weight,
            vehicle.eta,
        )
        for vehicle in problem.vehicles
    ] == EXPECTED_VEHICLES
    assert len({vehicle.id for vehicle in problem.vehicles}) == 16
    assert all(vehicle.orientation.value == "horizontal" for vehicle in problem.vehicles)


def test_reference16_seeded_initial_state_satisfies_constraints() -> None:
    problem = load_problem(PROBLEM_PATH)
    initial_state = create_random_initial_state(problem, seed=42)

    assert len(initial_state.vehicles) == 16
    assert is_valid_state(initial_state)
