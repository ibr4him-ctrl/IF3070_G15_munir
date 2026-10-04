from importlib import import_module

from munir.core.models import Orientation, Ship, State, Vehicle
from munir.experiments.runner import ExperimentRun


def test_state_figure_respects_orientation_and_lists_loaded_and_unloaded():
    plot = import_module("munir.visualization.plots")
    state = State(
        Ship(5, 4, 10),
        [
            Vehicle("A", 1, 3, 20, 2, 0, Orientation.VERTICAL, 1, 1),
            Vehicle("B", 2, 2, 40, 3, 0),
        ],
        value=20,
    )
    figure = plot.plot_state(state, "Initial state")
    rectangle = figure.axes[0].patches[0]
    assert rectangle.get_xy() == (1, 1)
    assert rectangle.get_width() == 3
    assert rectangle.get_height() == 1
    labels = " ".join(text.get_text() for ax in figure.axes for text in ax.texts)
    assert "A" in labels and "B" in labels and "vertical" in labels
    assert "Di luar" in labels and "Di dalam" in labels
    assert "20" in figure.axes[0].get_title()


def test_graphs_use_recorded_values_and_correct_iteration_indices():
    plot = import_module("munir.visualization.plots")
    run = ExperimentRun(
        1,
        2,
        0.1,
        [10, 0, 20],
        20,
        State(Ship(1, 1, 1)),
        best_objective_history=[10, 10, 20],
        temperature_history=[10, 10, 5],
        acceptance_probability_history=[None, 0.4, 1],
    )
    figure = plot.plot_objective(run, "simulated_annealing")
    assert list(figure.axes[0].lines[0].get_ydata()) == [10, 0, 20]
    assert list(figure.axes[0].lines[1].get_ydata()) == [10, 10, 20]
    annealing = plot.plot_annealing(run)
    assert list(annealing.axes[0].lines[0].get_ydata()) == [10, 5]
    assert list(annealing.axes[1].lines[0].get_xdata()) == [1, 2]
    assert list(annealing.axes[1].lines[0].get_ydata()) == [0.4, 1]
    run.average_history = [5, 6, 9]
    ga = plot.plot_objective(run, "genetic_algorithm")
    assert list(ga.axes[0].lines[1].get_ydata()) == [5, 6, 9]
    assert ga.axes[0].get_xlabel() == "Generasi"
