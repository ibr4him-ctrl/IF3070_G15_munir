from pathlib import Path
from typing import TYPE_CHECKING

from matplotlib import colormaps
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator

from munir.core.models import State

if TYPE_CHECKING:
    from munir.experiments.runner import ExperimentRun


def plot_state(state: State, title: str) -> Figure:
    height = max(5.5, 2.8 + len(state.vehicles) * 0.32)
    figure = Figure(figsize=(12, height), layout="constrained")
    FigureCanvasAgg(figure)
    deck, inventory = figure.subplots(1, 2, gridspec_kw={"width_ratios": [1.1, 1]})
    deck.set(
        xlim=(0, state.ship.width),
        ylim=(0, state.ship.length),
        xlabel="x (width / grid)",
        ylabel="y (length / grid)",
        aspect="equal",
    )
    deck.xaxis.set_major_locator(MaxNLocator(integer=True))
    deck.yaxis.set_major_locator(MaxNLocator(integer=True))
    if max(state.ship.width, state.ship.length) <= 100:
        deck.set_xticks(range(state.ship.width + 1), minor=True)
        deck.set_yticks(range(state.ship.length + 1), minor=True)
    deck.grid(which="both", color="#d1d5db", linewidth=0.5)
    deck.set_axisbelow(True)
    weight = sum(v.weight for v in state.vehicles if v.is_loaded)
    deck.set_title(
        f"{title}\nObjective: {state.value:g} | Berat: {weight:g}/{state.ship.max_capacity:g}",
        fontsize=12,
        pad=14,
    )
    inventory.axis("off")
    vehicles = sorted(state.vehicles, key=lambda vehicle: vehicle.id)
    colors = {v.id: colormaps["tab20"](i % 20) for i, v in enumerate(vehicles)}
    for vehicle in vehicles:
        if vehicle.is_loaded:
            deck.add_patch(
                Rectangle(
                    (vehicle.x, vehicle.y),
                    vehicle.occupied_width,
                    vehicle.occupied_length,
                    facecolor=colors[vehicle.id],
                    edgecolor="#1f2937",
                    linewidth=1.2,
                    alpha=0.85,
                )
            )
            deck.text(
                vehicle.x + vehicle.occupied_width / 2,
                vehicle.y + vehicle.occupied_length / 2,
                f"{vehicle.id}\n{vehicle.orientation.value[0].upper()}",
                ha="center",
                va="center",
                fontsize=9,
            )
    lines = ["Di dalam kapal:"]
    loaded = [v for v in vehicles if v.is_loaded]
    outside = [v for v in vehicles if not v.is_loaded]
    for v in loaded:
        lines.append(
            f"{v.id}: ({v.x}, {v.y}) {v.orientation.value} "
            f"{v.occupied_width}x{v.occupied_length} | fee {v.shipping_fee:g}"
        )
    if not loaded:
        lines.append("(tidak ada)")
    lines.extend(["", "Di luar kapal:"])
    for v in outside:
        lines.append(
            f"{v.id}: {v.orientation.value} "
            f"{v.occupied_width}x{v.occupied_length} | fee {v.shipping_fee:g}"
        )
    if not outside:
        lines.append("(tidak ada)")
    inventory.text(0, 1, "\n".join(lines), va="top", fontsize=10, linespacing=1.65)
    return figure


def plot_objective(run: "ExperimentRun", algorithm: str) -> Figure:
    figure = Figure(figsize=(9, 4.8), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots()
    ga = algorithm == "genetic_algorithm"
    axes.plot(
        run.objective_history,
        label="Fitness maksimum" if ga else "State saat ini",
        color="#2563eb",
        linewidth=1.5,
    )
    if ga and run.average_history is not None:
        axes.plot(run.average_history, label="Fitness rata-rata", color="#ea580c")
    elif run.best_objective_history is not None:
        axes.plot(
            run.best_objective_history, label="Terbaik sejauh ini", color="#ea580c", linestyle="--"
        )
    axes.set(
        xlabel="Generasi" if ga else "Iterasi",
        ylabel="Shipping fee",
        title=f"{algorithm} | Run {run.run} | Seed {run.seed}",
    )
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes.grid(alpha=0.25)
    axes.legend()
    return figure


def plot_annealing(run: "ExperimentRun") -> Figure:
    figure = Figure(figsize=(9, 6), layout="constrained")
    FigureCanvasAgg(figure)
    temperature_axes, probability_axes = figure.subplots(2, 1, sharex=True)
    temperatures = run.temperature_history or []
    probabilities = run.acceptance_probability_history or []
    temperature_axes.plot(range(1, len(temperatures)), temperatures[1:], color="#2563eb")
    probability_axes.plot(
        range(1, len(probabilities)), probabilities[1:], color="#7c3aed", linewidth=0.9
    )
    temperature_axes.set(
        ylabel="Temperature", title=f"Simulated Annealing | Run {run.run} | Seed {run.seed}"
    )
    probability_axes.set(xlabel="Iterasi", ylabel="Acceptance probability", ylim=(-0.03, 1.03))
    for axes in [temperature_axes, probability_axes]:
        axes.grid(alpha=0.25)
        axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    return figure


def save_run_plots(run: "ExperimentRun", algorithm: str, directory: Path) -> None:
    prefix = f"run_{run.run:02d}"
    figures = [
        ("final", plot_state(run.final_state, f"Final state | Run {run.run}")),
        ("objective", plot_objective(run, algorithm)),
    ]
    if run.initial_state is not None:
        figures.append(("initial", plot_state(run.initial_state, f"Initial state | Run {run.run}")))
    if run.temperature_history is not None:
        figures.append(("annealing", plot_annealing(run)))
    for name, figure in figures:
        figure.savefig(directory / f"{prefix}_{name}.png", dpi=140)
        figure.clear()
