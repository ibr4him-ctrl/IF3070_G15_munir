from munir.core.models import Ship, Vehicle


def occupied_cells(vehicle: Vehicle) -> set[tuple[int, int]]:
    if not vehicle.is_loaded:
        return set()

    return {
        (vehicle.x + x, vehicle.y + y)
        for x in range(vehicle.occupied_width)
        for y in range(vehicle.occupied_length)
    }


def is_inside_ship(vehicle: Vehicle, ship: Ship) -> bool:
    if not vehicle.is_loaded:
        return False

    return (
        vehicle.x >= 0
        and vehicle.y >= 0
        and vehicle.x + vehicle.occupied_width <= ship.width
        and vehicle.y + vehicle.occupied_length <= ship.length
    )
