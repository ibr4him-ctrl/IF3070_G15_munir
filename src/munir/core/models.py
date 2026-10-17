from dataclasses import dataclass, field
from enum import Enum


# StrEnum changes str(member); retain the existing representation for API compatibility.
class Orientation(str, Enum):  # noqa: UP042
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(slots=True)
class Vehicle:
    id: str
    width: int
    length: int
    shipping_fee: float
    weight: float
    eta: int
    orientation: Orientation = Orientation.HORIZONTAL
    x: int | None = None
    y: int | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Vehicle id cannot be empty")
        if self.width <= 0 or self.length <= 0:
            raise ValueError("Vehicle dimensions must be positive")
        if self.shipping_fee < 0:
            raise ValueError("Shipping fee cannot be negative")
        if self.weight <= 0:
            raise ValueError("Vehicle weight must be positive")
        if self.eta < 0:
            raise ValueError("ETA cannot be negative")
        if (self.x is None) != (self.y is None):
            raise ValueError("Vehicle coordinates must both be set or both be empty")

    @property
    def is_loaded(self) -> bool:
        return self.x is not None and self.y is not None

    @property
    def occupied_width(self) -> int:
        if self.orientation == Orientation.HORIZONTAL:
            return self.width
        return self.length

    @property
    def occupied_length(self) -> int:
        if self.orientation == Orientation.HORIZONTAL:
            return self.length
        return self.width


@dataclass(frozen=True, slots=True)
class Ship:
    width: int
    length: int
    max_capacity: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.length <= 0:
            raise ValueError("Ship dimensions must be positive")
        if self.max_capacity <= 0:
            raise ValueError("Ship capacity must be positive")


@dataclass(slots=True)
class State:
    ship: Ship
    vehicles: list[Vehicle] = field(default_factory=list)
    value: float = 0.0

    def __post_init__(self) -> None:
        vehicle_ids = [vehicle.id for vehicle in self.vehicles]
        if len(vehicle_ids) != len(set(vehicle_ids)):
            raise ValueError("Vehicle ids must be unique")
