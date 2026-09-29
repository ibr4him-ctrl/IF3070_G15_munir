import random
from copy import deepcopy

from munir.core.constraints import is_valid_state
from munir.core.models import Orientation, State, Vehicle
from munir.core.objective import update_state_value


def _find_vehicle(state: State, vehicle_id: str) -> Vehicle:
    for vehicle in state.vehicles:
        if vehicle.id == vehicle_id:
            return vehicle
    raise ValueError(f"Vehicle not found: {vehicle_id}")


def _finish(candidate: State) -> State:
    if not is_valid_state(candidate):
        raise ValueError("Neighbor state violates constraints")
    update_state_value(candidate)
    return candidate


def move_vehicle(
    state: State,
    vehicle_id: str,
    x: int | None,
    y: int | None,
) -> State:
    if (x is None) != (y is None):
        raise ValueError("Coordinates must both be set or both be empty")

    candidate = deepcopy(state)
    vehicle = _find_vehicle(candidate, vehicle_id)

    if (vehicle.x, vehicle.y) == (x, y):
        raise ValueError("Vehicle must move to a different position")

    vehicle.x = x
    vehicle.y = y
    return _finish(candidate)


def swap_vehicles(state: State, first_id: str, second_id: str) -> State:
    if first_id == second_id:
        raise ValueError("Vehicles must be different")

    candidate = deepcopy(state)
    first = _find_vehicle(candidate, first_id)
    second = _find_vehicle(candidate, second_id)

    if (first.x, first.y) == (second.x, second.y):
        raise ValueError("Vehicles must have different positions")

    first.x, second.x = second.x, first.x
    first.y, second.y = second.y, first.y
    return _finish(candidate)


def rotate_vehicle(state: State, vehicle_id: str) -> State:
    candidate = deepcopy(state)
    vehicle = _find_vehicle(candidate, vehicle_id)

    if vehicle.orientation == Orientation.HORIZONTAL:
        vehicle.orientation = Orientation.VERTICAL
    else:
        vehicle.orientation = Orientation.HORIZONTAL

    return _finish(candidate)


def random_neighbor(
    state: State,
    rng: random.Random,
    max_attempts: int = 100,
) -> State:
    if not state.vehicles:
        raise ValueError("State has no vehicles")

    operations = ["move", "rotate"]
    if len(state.vehicles) >= 2:
        operations.append("swap")

    for _ in range(max_attempts):
        operation = rng.choice(operations)

        try:
            if operation == "move":
                vehicle = rng.choice(state.vehicles)
                if rng.random() < 0.2:
                    return move_vehicle(state, vehicle.id, None, None)

                max_x = state.ship.width - vehicle.occupied_width
                max_y = state.ship.length - vehicle.occupied_length
                if max_x >= 0 and max_y >= 0:
                    return move_vehicle(
                        state,
                        vehicle.id,
                        rng.randint(0, max_x),
                        rng.randint(0, max_y),
                    )

            elif operation == "swap":
                first, second = rng.sample(state.vehicles, 2)
                return swap_vehicles(state, first.id, second.id)

            else:
                vehicle = rng.choice(state.vehicles)
                return rotate_vehicle(state, vehicle.id)
        except ValueError:
            continue

    raise RuntimeError("Could not generate a valid neighbor")
