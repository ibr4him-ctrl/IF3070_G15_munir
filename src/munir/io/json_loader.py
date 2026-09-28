import json
from pathlib import Path
from typing import Any

from munir.core.models import Orientation, Ship, State, Vehicle
from munir.experiments.config import ExperimentConfig


def _read_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"File not found: {file_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {file_path}: {error.msg}") from error

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")

    return data


def _get(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    raise ValueError(f"Missing field: {keys[0]}")


def _dimensions(data: dict[str, Any]) -> tuple[int, int]:
    dimensions = _get(data, "dimensions", "Dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("Dimensions must be an object")

    width = _get(dimensions, "width", "w")
    length = _get(dimensions, "length", "l")
    return int(width), int(length)


def load_problem(path: str | Path) -> State:
    data = _read_json(path)
    ship_data = _get(data, "ship", "Ship")
    vehicle_data = _get(data, "vehicles", "Vehicles")

    if not isinstance(ship_data, dict):
        raise ValueError("Ship must be an object")
    if not isinstance(vehicle_data, list):
        raise ValueError("Vehicles must be an array")

    ship_width, ship_length = _dimensions(ship_data)
    ship = Ship(
        width=ship_width,
        length=ship_length,
        max_capacity=float(_get(ship_data, "max_capacity", "maxCapacity", "MaxCapacity")),
    )

    vehicles = []
    for item in vehicle_data:
        if not isinstance(item, dict):
            raise ValueError("Each vehicle must be an object")

        width, length = _dimensions(item)
        position = item.get("position", {})
        if not isinstance(position, dict):
            raise ValueError("Vehicle position must be an object")

        vehicles.append(
            Vehicle(
                id=str(_get(item, "id")),
                width=width,
                length=length,
                shipping_fee=float(_get(item, "shipping_fee", "shippingFee", "ShippingFee")),
                weight=float(_get(item, "weight", "Weight")),
                eta=int(_get(item, "eta", "ETA")),
                orientation=Orientation(str(item.get("orientation", "horizontal")).lower()),
                x=position.get("x"),
                y=position.get("y"),
            )
        )

    return State(ship=ship, vehicles=vehicles)


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    data = _read_json(path)

    return ExperimentConfig(
        algorithm=str(_get(data, "algorithm")),
        runs=int(data.get("runs", 3)),
        max_iterations=int(data.get("max_iterations", 1000)),
        random_seed=data.get("random_seed"),
        output_dir=Path(data.get("output_dir", "output")),
        parameters=dict(data.get("parameters", {})),
    )
