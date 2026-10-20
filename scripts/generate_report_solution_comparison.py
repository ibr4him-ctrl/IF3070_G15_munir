"""Render a side-by-side view of each algorithm's best recorded final layout."""

from __future__ import annotations

import json
import math
from pathlib import Path

from matplotlib import colormaps
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
RUN_DIRS = {
    "Hill Climbing": ROOT / "output/adham/stochastic_hill_climbing_20261004_194425",
    "Simulated Annealing": ROOT / "output/adham/simulated_annealing_20261004_194427",
    "Genetic Algorithm": ROOT / "output/reyna/genetic_algorithm_20261017_210648",
}
OUTPUT = ROOT / "docs/assets/tahap4_layout_comparison.png"


def best_run(directory: Path) -> dict[str, object]:
    paths = directory.glob("run_*.json")
    results = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if not results:
        raise ValueError(f"No run JSON files in {directory}")
    return max(results, key=lambda result: (float(result["final_objective"]), -result["run"]))


def validate_final_state(result: dict[str, object]) -> None:
    """Refuse to draw a final layout unless it satisfies project constraints."""
    state = result["final_state"]
    ship = state["ship"]
    occupied: set[tuple[int, int]] = set()
    loaded_weight = 0.0
    loaded_fee = 0.0

    for vehicle in state["vehicles"]:
        if vehicle["orientation"] not in {"horizontal", "vertical"}:
            raise ValueError(f"Run {result['run']} has an unknown vehicle orientation")
        x, y = vehicle["x"], vehicle["y"]
        if (x is None) != (y is None):
            raise ValueError(f"Run {result['run']} has a partial vehicle position")
        if x is None:
            continue

        width, length = int(vehicle["width"]), int(vehicle["length"])
        if vehicle["orientation"] == "vertical":
            width, length = length, width
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x + width > ship["width"] or y + length > ship["length"]:
            raise ValueError(f"Run {result['run']} has a vehicle outside the deck")

        cells = {
            (column, row)
            for column in range(x, x + width)
            for row in range(y, y + length)
        }
        if occupied.intersection(cells):
            raise ValueError(f"Run {result['run']} has overlapping vehicles")
        occupied.update(cells)
        loaded_weight += float(vehicle["weight"])
        loaded_fee += float(vehicle["shipping_fee"])

    if loaded_weight > float(ship["max_capacity"]):
        raise ValueError(f"Run {result['run']} exceeds ship capacity")
    if not math.isclose(loaded_fee, float(result["final_objective"]), abs_tol=1e-9):
        raise ValueError(f"Run {result['run']} objective does not match loaded vehicle fees")
    if not math.isclose(float(state["value"]), loaded_fee, abs_tol=1e-9):
        raise ValueError(f"Run {result['run']} final state and objective do not match")


def render() -> None:
    figure = Figure(figsize=(13.5, 7.2), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(1, 3)
    selected_runs = [(algorithm, best_run(directory)) for algorithm, directory in RUN_DIRS.items()]
    for _, result in selected_runs:
        validate_final_state(result)
    vehicle_ids = sorted(
        {
            vehicle["id"]
            for _, result in selected_runs
            for vehicle in result["final_state"]["vehicles"]
        }
    )
    color_index = {vehicle_id: index for index, vehicle_id in enumerate(vehicle_ids)}

    for axis, (algorithm, result) in zip(axes, selected_runs, strict=True):
        state = result["final_state"]
        ship = state["ship"]
        vehicles = sorted(state["vehicles"], key=lambda vehicle: vehicle["id"])
        axis.set(
            xlim=(0, ship["width"]),
            ylim=(0, ship["length"]),
            xlabel="Lebar geladak (petak)",
            ylabel="Panjang geladak (petak)",
            aspect="equal",
            title=(
                f"{algorithm}\nRun {result['run']} · seed {result['seed']} · "
                f"objective {result['final_objective']:g}"
            ),
        )
        axis.set_xticks(range(ship["width"] + 1))
        axis.set_yticks(range(ship["length"] + 1))
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.yaxis.set_major_locator(MaxNLocator(integer=True))
        axis.grid(color="#cbd5e1", linewidth=0.75)
        axis.set_axisbelow(True)

        loaded = [vehicle for vehicle in vehicles if vehicle["x"] is not None]
        for vehicle in loaded:
            width, length = vehicle["width"], vehicle["length"]
            if vehicle["orientation"] == "vertical":
                width, length = length, width
            axis.add_patch(
                Rectangle(
                    (vehicle["x"], vehicle["y"]),
                    width,
                    length,
                    facecolor=colormaps["tab20"](color_index[vehicle["id"]] % 20),
                    edgecolor="#172554",
                    linewidth=1.0,
                    alpha=0.85,
                )
            )
            axis.text(
                vehicle["x"] + width / 2,
                vehicle["y"] + length / 2,
                vehicle["id"],
                ha="center",
                va="center",
                fontsize=8,
            )

    figure.suptitle("Layout solusi final terbaik yang tersimpan per algoritma", fontsize=15)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=180)


if __name__ == "__main__":
    render()
