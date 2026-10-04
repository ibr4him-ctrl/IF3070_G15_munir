from munir.core.models import Ship, State, Vehicle
from munir.core.objective import calculate_objective


def test_objective_counts_only_valid_loaded_vehicles() -> None:
    state = State(
        ship=Ship(width=4, length=4, max_capacity=10),
        vehicles=[
            Vehicle("valid", 2, 2, 100, 4, 1, x=0, y=0),
            Vehicle("overlap", 2, 2, 80, 3, 1, x=1, y=1),
            Vehicle("outside", 2, 2, 70, 2, 1, x=3, y=3),
            Vehicle("unloaded", 1, 1, 50, 1, 1),
        ],
    )

    assert calculate_objective(state) == 100


def test_objective_respects_capacity() -> None:
    state = State(
        ship=Ship(width=4, length=4, max_capacity=5),
        vehicles=[
            Vehicle("first", 1, 1, 60, 4, 1, x=0, y=0),
            Vehicle("too-heavy", 1, 1, 90, 2, 1, x=2, y=2),
        ],
    )

    assert calculate_objective(state) == 60
