from munir.core.constraints import constraint_violations, is_valid_state
from munir.core.models import Ship, State, Vehicle


def test_valid_state_passes_all_constraints() -> None:
    state = State(
        ship=Ship(width=4, length=4, max_capacity=10),
        vehicles=[
            Vehicle("loaded", 2, 2, 100, 4, 1, x=0, y=0),
            Vehicle("unloaded", 1, 1, 50, 2, 1),
        ],
    )

    assert is_valid_state(state)
    assert constraint_violations(state) == []


def test_constraint_violations_report_invalid_placements() -> None:
    state = State(
        ship=Ship(width=4, length=4, max_capacity=5),
        vehicles=[
            Vehicle("first", 2, 2, 100, 4, 1, x=0, y=0),
            Vehicle("overlap", 2, 2, 80, 3, 1, x=1, y=1),
            Vehicle("outside", 2, 2, 70, 1, 1, x=3, y=3),
        ],
    )

    assert set(constraint_violations(state)) == {
        "out_of_bounds",
        "overlap",
        "capacity_exceeded",
    }
