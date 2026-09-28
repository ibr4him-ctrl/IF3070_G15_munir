from munir.core.models import State
from munir.core.placement import is_inside_ship, occupied_cells


def vehicles_are_inside_ship(state: State) -> bool:
    return all(
        not vehicle.is_loaded or is_inside_ship(vehicle, state.ship)
        for vehicle in state.vehicles
    )


def unloaded_vehicles_are_outside(state: State) -> bool:
    return all(
        (vehicle.x is None and vehicle.y is None)
        or (vehicle.x is not None and vehicle.y is not None)
        for vehicle in state.vehicles
    )


def has_no_overlap(state: State) -> bool:
    used_cells: set[tuple[int, int]] = set()

    for vehicle in state.vehicles:
        if not vehicle.is_loaded:
            continue

        cells = occupied_cells(vehicle)
        if used_cells.intersection(cells):
            return False
        used_cells.update(cells)

    return True


def is_within_capacity(state: State) -> bool:
    total_weight = sum(
        vehicle.weight
        for vehicle in state.vehicles
        if vehicle.is_loaded
    )
    return total_weight <= state.ship.max_capacity


def constraint_violations(state: State) -> list[str]:
    violations = []

    if not unloaded_vehicles_are_outside(state):
        violations.append("invalid_outside_position")
    if not vehicles_are_inside_ship(state):
        violations.append("out_of_bounds")
    if not has_no_overlap(state):
        violations.append("overlap")
    if not is_within_capacity(state):
        violations.append("capacity_exceeded")

    return violations


def is_valid_state(state: State) -> bool:
    return not constraint_violations(state)
