"""Create the Tahap 3 comparison from the checked-in experiment artefacts.

This script reads results only; it never runs an optimizer or modifies the
source experiment directories.  Run from the repository root:

    python scripts/generate_algorithm_comparison.py
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "Hill Climbing": ROOT / "output/adham/stochastic_hill_climbing_20261004_194425",
    "Simulated Annealing": ROOT / "output/adham/simulated_annealing_20261004_194427",
    "Genetic Algorithm": ROOT / "output/reyna/genetic_algorithm_20261017_210648",
}
OUTPUT_CSV = ROOT / "docs/tahap_3_comparison.csv"
OUTPUT_PNG = ROOT / "docs/assets/tahap_3_algorithm_comparison.png"


@dataclass(frozen=True)
class Metrics:
    algorithm: str
    runs: int
    seeds: str
    best_objective: float
    average_final_objective: float
    worst_final_objective: float
    valid_solutions: int
    average_runtime_seconds: float
    average_iterations: float


def state_is_valid(state: dict[str, object]) -> bool:
    """Validate the serialized final state using the project's four constraints."""
    ship = state["ship"]
    vehicles = state["vehicles"]
    max_capacity = float(ship["max_capacity"])
    width, length = int(ship["width"]), int(ship["length"])
    occupied: set[tuple[int, int]] = set()
    total_weight = 0.0

    for vehicle in vehicles:
        x, y = vehicle["x"], vehicle["y"]
        if (x is None) != (y is None):
            return False
        if x is None:
            continue
        x, y = int(x), int(y)
        vehicle_width, vehicle_length = int(vehicle["width"]), int(vehicle["length"])
        if vehicle["orientation"] == "vertical":
            vehicle_width, vehicle_length = vehicle_length, vehicle_width
        if x < 0 or y < 0 or x + vehicle_width > width or y + vehicle_length > length:
            return False
        cells = {
            (column, row)
            for column in range(x, x + vehicle_width)
            for row in range(y, y + vehicle_length)
        }
        if occupied.intersection(cells):
            return False
        occupied.update(cells)
        total_weight += float(vehicle["weight"])
    return total_weight <= max_capacity


def load_metrics(name: str, directory: Path) -> Metrics:
    paths = sorted(directory.glob("run_*.json"))
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if not runs:
        raise ValueError(f"No run JSON files found in {directory}")
    objectives = [float(run["final_objective"]) for run in runs]
    return Metrics(
        algorithm=name,
        runs=len(runs),
        seeds=", ".join(str(run["seed"]) for run in runs),
        best_objective=max(objectives),
        average_final_objective=mean(objectives),
        worst_final_objective=min(objectives),
        valid_solutions=sum(state_is_valid(run["final_state"]) for run in runs),
        average_runtime_seconds=mean(float(run["duration_seconds"]) for run in runs),
        average_iterations=mean(float(run["iterations"]) for run in runs),
    )


def write_csv(metrics: list[Metrics]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(Metrics.__dataclass_fields__)
        for row in metrics:
            writer.writerow(
                [
                    row.algorithm,
                    row.runs,
                    row.seeds,
                    f"{row.best_objective:.2f}",
                    f"{row.average_final_objective:.2f}",
                    f"{row.worst_final_objective:.2f}",
                    f"{row.valid_solutions}/{row.runs}",
                    f"{row.average_runtime_seconds:.6f}",
                    f"{row.average_iterations:.2f}",
                ]
            )


def write_plot(metrics: list[Metrics]) -> None:
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    names = [metric.algorithm for metric in metrics]
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].bar(names, [metric.average_final_objective for metric in metrics], color="#2563eb")
    axes[0].set(title="Rata-rata objective final", ylabel="Objective")
    axes[1].bar(names, [metric.best_objective for metric in metrics], color="#ea580c")
    axes[1].set(title="Objective terbaik", ylabel="Objective")
    for axis in axes:
        axis.tick_params(axis="x", rotation=12)
        axis.grid(axis="y", alpha=0.25)
    figure.suptitle("Tahap 3 — Perbandingan hasil eksperimen tersimpan (n=3)")
    figure.tight_layout()
    figure.savefig(OUTPUT_PNG, dpi=160)
    plt.close(figure)


def main() -> None:
    metrics = [load_metrics(name, directory) for name, directory in SOURCES.items()]
    write_csv(metrics)
    write_plot(metrics)
    for metric in metrics:
        print(metric)


if __name__ == "__main__":
    main()
