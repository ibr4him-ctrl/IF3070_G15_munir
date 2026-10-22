from pathlib import Path
from typing import TYPE_CHECKING

from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator

from munir.core.models import State

if TYPE_CHECKING:
    from munir.experiments.runner import ExperimentRun


def _draw_deck(axes: Axes, state: State, title: str, colors: dict) -> None:
    axes.set(
        xlim=(0, state.ship.width),
        ylim=(0, state.ship.length),
        aspect="equal",
        xlabel="x",
        ylabel="y",
        title=f"{title}\nNilai {state.value:g}",
    )
    axes.set_xticks(range(state.ship.width + 1))
    axes.set_yticks(range(state.ship.length + 1))
    axes.grid(color="#d1d5db", linewidth=0.5, alpha=0.7)
    axes.set_axisbelow(True)
    axes.tick_params(labelsize=8)
    for vehicle in state.vehicles:
        if not vehicle.is_loaded:
            continue
        axes.add_patch(
            Rectangle(
                (vehicle.x, vehicle.y),
                vehicle.occupied_width,
                vehicle.occupied_length,
                facecolor=colors[vehicle.id],
                edgecolor="#374151",
                linewidth=0.8,
                alpha=0.85,
            )
        )
        axes.text(
            vehicle.x + vehicle.occupied_width / 2,
            vehicle.y + vehicle.occupied_length / 2,
            f"{vehicle.id}\n{vehicle.orientation.value[0].upper()}",
            ha="center",
            va="center",
            fontsize=8,
        )
    outside = ", ".join(sorted(v.id for v in state.vehicles if not v.is_loaded)) or "-"
    axes.text(
        0.5,
        -0.14,
        f"Di luar: {outside}",
        transform=axes.transAxes,
        ha="center",
        va="top",
        fontsize=7,
        wrap=True,
    )


def plot_report_run(
    run: "ExperimentRun", algorithm: str, upper_bound: float | None = None
) -> Figure:
    if run.initial_state is None:
        raise ValueError("Report figures require an initial state")
    figure = Figure(figsize=(10, 8.4))
    FigureCanvasAgg(figure)
    grid = figure.add_gridspec(2, 2, height_ratios=[2.3, 1], hspace=0.43, wspace=0.28)
    figure.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.12)
    initial_axes = figure.add_subplot(grid[0, 0])
    final_axes = figure.add_subplot(grid[0, 1])
    history_axes = figure.add_subplot(grid[1, :])
    colors = {
        vehicle.id: colormaps["tab20"](i % 20)
        for i, vehicle in enumerate(sorted(run.initial_state.vehicles, key=lambda v: v.id))
    }
    _draw_deck(initial_axes, run.initial_state, "State awal", colors)
    _draw_deck(final_axes, run.final_state, "State akhir terbaik", colors)
    history_axes.plot(run.objective_history, label="State saat ini", linewidth=1.1)
    if algorithm == "simulated_annealing" and run.best_objective_history is not None:
        history_axes.plot(
            run.best_objective_history, label="Terbaik sejauh ini", color="#ea580c", linewidth=1.2
        )
    if upper_bound is not None:
        history_axes.axhline(
            upper_bound,
            label=f"Batas atas knapsack berat {upper_bound:g}",
            color="#6b7280",
            linestyle=":",
            linewidth=1.1,
        )
    history_axes.set(xlabel="Iterasi", ylabel="ShippingFee (juta rupiah)")
    history_axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    history_axes.tick_params(labelsize=8)
    history_axes.grid(alpha=0.2)
    history_axes.legend(fontsize=8, loc="best")
    name = (
        "Simulated Annealing" if algorithm == "simulated_annealing" else "Stochastic Hill-Climbing"
    )
    figure.suptitle(f"{name} | Percobaan {run.run}", fontsize=14, fontweight="bold")
    figure.text(
        0.5,
        0.025,
        f"Seed {run.seed} | F awal {run.initial_state.value:g} | "
        f"F akhir {run.final_objective:g} | Iterasi {run.iterations} | "
        f"Waktu {run.duration_seconds:.4f} detik",
        ha="center",
        fontsize=10,
    )
    return figure


def plot_ga_report_run(
    run: "ExperimentRun",
    upper_bound: float | None = None,
    configuration_name: str | None = None,
) -> Figure:
    if run.initial_state is None:
        raise ValueError("GA report figures require an initial state")
    if run.population_size is None:
        raise ValueError("GA report figures require a population size")
    if len(run.objective_history) != run.iterations + 1:
        raise ValueError("GA maximum history must include generation zero and every generation")
    if run.average_history is None or len(run.average_history) != len(run.objective_history):
        raise ValueError("GA average history must match the maximum history")

    figure = Figure(figsize=(10, 8.4), facecolor="white")
    figure.patch.set_edgecolor("#374151")
    figure.patch.set_linewidth(0.8)
    FigureCanvasAgg(figure)
    grid = figure.add_gridspec(2, 2, height_ratios=[2.3, 1], hspace=0.43, wspace=0.28)
    figure.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.12)
    initial_axes = figure.add_subplot(grid[0, 0])
    final_axes = figure.add_subplot(grid[0, 1])
    history_axes = figure.add_subplot(grid[1, :])
    colors = {
        vehicle.id: colormaps["tab20"](i % 20)
        for i, vehicle in enumerate(sorted(run.initial_state.vehicles, key=lambda v: v.id))
    }
    _draw_deck(initial_axes, run.initial_state, "State awal", colors)
    _draw_deck(final_axes, run.final_state, "State akhir terbaik", colors)

    generations = range(len(run.objective_history))
    history_axes.plot(
        generations,
        run.objective_history,
        label="Maksimum populasi",
        color="#2563eb",
        linewidth=1.1,
    )
    history_axes.plot(
        generations,
        run.average_history,
        label="Rata-rata populasi",
        color="#ea580c",
        linewidth=1.1,
    )
    if upper_bound is not None:
        history_axes.axhline(
            upper_bound,
            label=f"Batas atas knapsack berat {upper_bound:g}",
            color="#6b7280",
            linestyle=":",
            linewidth=1.1,
        )
    history_axes.set(
        xlabel="Generasi",
        ylabel="ShippingFee (juta rupiah)",
        xlim=(0, run.iterations),
    )
    history_axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    history_axes.tick_params(labelsize=8)
    history_axes.grid(alpha=0.2)
    history_axes.legend(fontsize=8, loc="best")

    config_label = configuration_name or f"G={run.iterations}, P={run.population_size}"
    figure.suptitle(
        f"Genetic Algorithm | {config_label} | Percobaan {run.run}",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.025,
        f"Seed {run.seed} | F awal {run.initial_state.value:g} | "
        f"F akhir {run.final_objective:g} | Generasi {run.iterations} | "
        f"Waktu {run.duration_seconds:.4f} detik",
        ha="center",
        fontsize=10,
    )
    return figure


def save_ga_report_plot(
    run: "ExperimentRun",
    directory: Path,
    upper_bound: float | None,
    configuration_name: str | None = None,
) -> None:
    figure = plot_ga_report_run(run, upper_bound, configuration_name)
    figure.savefig(directory / f"run_{run.run:02d}_report.png", dpi=160)
    figure.clear()


def plot_diagnostics(run: "ExperimentRun") -> Figure:
    if run.temperature_history is None or run.acceptance_probability_history is None:
        raise ValueError("SA diagnostics require recorded temperatures and probabilities")
    figure = Figure(figsize=(10, 3.6), layout="constrained")
    FigureCanvasAgg(figure)
    probabilities, temperatures = figure.subplots(1, 2)
    indices = range(1, len(run.temperature_history))
    probabilities.plot(indices, run.acceptance_probability_history[1:], linewidth=0.7)
    temperatures.plot(indices, run.temperature_history[1:], linewidth=1.1)
    probabilities.set(
        xlabel="Iterasi",
        ylabel="Penerimaan min(1, exp(delta/T))",
        ylim=(-0.03, 1.03),
        title="Probabilitas penerimaan",
    )
    temperatures.set(xlabel="Iterasi", ylabel="Temperatur T", title="Jadwal temperatur")
    for axes in [probabilities, temperatures]:
        axes.xaxis.set_major_locator(MaxNLocator(integer=True))
        axes.grid(alpha=0.25)
        axes.tick_params(labelsize=8)
    figure.suptitle(f"Simulated Annealing | Seed {run.seed}", fontsize=12)
    return figure


def save_hc_sa_plots(
    run: "ExperimentRun", algorithm: str, directory: Path, upper_bound: float | None
) -> None:
    figure = plot_report_run(run, algorithm, upper_bound)
    figure.savefig(directory / f"run_{run.run:02d}_report.png", dpi=160)
    figure.clear()
    if algorithm == "simulated_annealing":
        diagnostics = plot_diagnostics(run)
        diagnostics.savefig(directory / f"run_{run.run:02d}_diagnostics.png", dpi=160)
        diagnostics.clear()
