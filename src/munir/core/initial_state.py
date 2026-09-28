import random
from copy import deepcopy

from munir.core.models import Orientation, State
from munir.core.objective import update_state_value
from munir.core.placement import occupied_cells


def create_random_initial_state(problem: State, seed: int | None = None) -> State:
    rng = random.Random(seed)
    vehicles = deepcopy(problem.vehicles)
    rng.shuffle(vehicles)

    state = State(ship=problem.ship, vehicles=vehicles)
    used_cells: set[tuple[int, int]] = set()
    total_weight = 0.0

    for vehicle in state.vehicles:
        vehicle.x = None
        vehicle.y = None
        vehicle.orientation = rng.choice(list(Orientation))

        if total_weight + vehicle.weight > state.ship.max_capacity:
            continue

        max_x = state.ship.width - vehicle.occupied_width
        max_y = state.ship.length - vehicle.occupied_length
        if max_x < 0 or max_y < 0:
            continue

        positions = [
            (x, y)
            for x in range(max_x + 1)
            for y in range(max_y + 1)
        ]
        rng.shuffle(positions)

        for x, y in positions:
            vehicle.x = x
            vehicle.y = y
            cells = occupied_cells(vehicle)

            if not used_cells.intersection(cells):
                used_cells.update(cells)
                total_weight += vehicle.weight
                break

        else:
            vehicle.x = None
            vehicle.y = None

    update_state_value(state)
    return state
