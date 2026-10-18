from dataclasses import dataclass, field
from pathlib import Path

ParameterValue = int | float | str | bool


@dataclass(slots=True)
class ExperimentConfig:
    algorithm: str
    runs: int = 3
    max_iterations: int = 1000
    random_seed: int | None = None
    output_dir: Path = Path("output")
    parameters: dict[str, ParameterValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.algorithm.strip():
            raise ValueError("Algorithm cannot be empty")
        if self.runs <= 0:
            raise ValueError("Runs must be positive")
        if self.max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive")

        self.output_dir = Path(self.output_dir)
