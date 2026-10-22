"""Validation and a weight-only relaxation for HC/SA experiment evidence."""

from munir.core.constraints import constraint_violations
from munir.core.models import State
from munir.core.objective import calculate_objective


def weight_upper_bound(problem: State) -> float | None:
    """Solve the 0/1 weight knapsack; ignoring geometry gives an upper bound.

    No bound is returned for fractional weights/capacity: integer DP would not
    represent those instances without an explicitly chosen rescaling. The
    optional bound is also skipped above five million DP cell updates.
    """
    if not float(problem.ship.max_capacity).is_integer() or any(
        not float(v.weight).is_integer() for v in problem.vehicles
    ):
        return None
    capacity = int(problem.ship.max_capacity)
    eligible = [v for v in problem.vehicles if v.weight <= capacity]
    if sum(v.weight for v in eligible) <= capacity:
        return sum(v.shipping_fee for v in eligible)
    if capacity * len(eligible) > 5_000_000:
        return None
    best = [0.0] * (capacity + 1)
    for vehicle in eligible:
        weight = int(vehicle.weight)
        for remaining in range(capacity, weight - 1, -1):
            best[remaining] = max(best[remaining], best[remaining - weight] + vehicle.shipping_fee)
    return best[capacity]


def validate_search_states(problem: State, initial: State, final: State, last: State) -> dict:
    """Reject invalid/stale results before exporting them as experiment evidence."""
    states = {"initial": initial, "final": final, "last": last}
    violations = {name: constraint_violations(state) for name, state in states.items()}
    expected_ids = {v.id for v in problem.vehicles}
    ids_preserved = all(
        len(state.vehicles) == len(problem.vehicles)
        and {v.id for v in state.vehicles} == expected_ids
        for state in states.values()
    )
    integer_coordinates = all(
        (v.x is None and v.y is None) or (type(v.x) is int and type(v.y) is int)
        for state in states.values()
        for v in state.vehicles
    )
    objective_matches = all(calculate_objective(state) == state.value for state in states.values())
    all_valid = (
        not any(violations.values()) and ids_preserved and integer_coordinates and objective_matches
    )
    result = {
        "all_valid": all_valid,
        "constraint_violations": violations,
        "vehicle_ids_preserved": ids_preserved,
        "integer_coordinates": integer_coordinates,
        "objective_matches": objective_matches,
        "final_recomputed_objective": calculate_objective(final),
    }
    if not all_valid:
        raise ValueError(f"HC/SA result validation failed: {result}")
    return result
