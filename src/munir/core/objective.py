from munir.core.models import State
from munir.core.placement import is_inside_ship, occupied_cells


def calculate_objective(state: State) -> float:
    used_cells: set[tuple[int, int]] = set()
    total_weight = 0.0
    total_fee = 0.0

    for vehicle in state.vehicles:
        if not is_inside_ship(vehicle, state.ship):
            continue

        cells = occupied_cells(vehicle)
        if used_cells.intersection(cells):
            continue
        if total_weight + vehicle.weight > state.ship.max_capacity:
            continue

        used_cells.update(cells)
        total_weight += vehicle.weight
        total_fee += vehicle.shipping_fee

    return total_fee


def update_state_value(state: State) -> float:
    state.value = calculate_objective(state)
    return state.value
