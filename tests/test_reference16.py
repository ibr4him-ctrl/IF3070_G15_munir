import csv
import hashlib
import json
import math
import tracemalloc
from dataclasses import asdict
from importlib import import_module

import pytest

from munir.algorithms.hill_climbing import stochastic_hill_climbing
from munir.algorithms.simulated_annealing import simulated_annealing
from munir.core.constraints import is_valid_state
from munir.core.initial_state import create_random_initial_state
from munir.core.models import Orientation, Ship, State, Vehicle
from munir.experiments.config import ExperimentConfig
from munir.experiments.runner import ExperimentRun, run_experiment
from munir.io.json_loader import load_experiment_config, load_problem


@pytest.mark.parametrize(
    "seed,initial_fee,hc_fee,hc_iterations,sa_fee,episodes,downhill",
    [
        (42, 824, 835, 186, 877, 2, (22, 209)),
        (43, 849, 856, 107, 863, 3, (20, 248)),
        (44, 822, 833, 110, 866, 3, (28, 242)),
    ],
)
def test_reference16_matches_report_without_changing_search(
    seed, initial_fee, hc_fee, hc_iterations, sa_fee, episodes, downhill
):
    problem = load_problem("configs/problem.reference16.json")
    initial = create_random_initial_state(problem, seed)
    hc = stochastic_hill_climbing(initial, max_no_improvement=100, seed=seed)
    sa = simulated_annealing(
        initial,
        initial_temperature=100,
        cooling_rate=0.995,
        min_temperature=0.01,
        max_iterations=1000,
        seed=seed,
    )
    assert initial.value == initial_fee
    assert (hc.final_state.value, hc.iterations) == (hc_fee, hc_iterations)
    assert (sa.final_state.value, sa.iterations) == (sa_fee, 1000)
    assert sa.stagnation_episodes == episodes
    assert (sa.accepted_worse, sa.rejected_worse) == downhill
    assert sa.accepted_candidates + sa.rejected_candidates == sa.iterations
    assert sa.accepted_candidates == sum(sa.accepted_history[1:])
    assert is_valid_state(hc.final_state) and is_valid_state(sa.final_state)
    assert len(sa.final_state.vehicles) == 16
    for i in range(1, sa.iterations + 1):
        assert sa.temperature_history[i] == 100 * 0.995 ** (i - 1)
        delta = sa.delta_history[i]
        expected = 1 if delta >= 0 else math.exp(delta / sa.temperature_history[i])
        assert sa.acceptance_probability_history[i] == pytest.approx(expected)


def test_stagnation_threshold_counts_once_and_bias_zero_preserves_trajectory():
    initial = State(Ship(1, 1, 1), [Vehicle("A", 1, 1, 10, 1, 0, x=0, y=0)])
    first = simulated_annealing(initial, max_iterations=250, seed=5)
    second = simulated_annealing(initial, max_iterations=250, seed=5, evaluation_bias=0)
    assert first.stagnation_episodes == 1
    assert first.stagnation_limit == 100
    assert first.no_improvement_history[-1] == 250
    left, right = asdict(first), asdict(second)
    left.pop("duration_seconds")
    right.pop("duration_seconds")
    assert left == right
    with pytest.raises(ValueError, match="evaluation_bias"):
        simulated_annealing(initial, evaluation_bias=1)


@pytest.mark.parametrize("algorithm", ["stochastic_hill_climbing", "simulated_annealing"])
def test_report_mode_exports_snapshots_validation_metrics_and_figures(tmp_path, algorithm):
    problem = load_problem("configs/problem.reference16.json")
    result = run_experiment(
        problem,
        ExperimentConfig(
            algorithm,
            runs=1,
            max_iterations=4,
            random_seed=42,
            output_dir=tmp_path,
            parameters={"plot_style": "report"},
        ),
    )
    folder = result.output_directory
    run = json.loads((folder / "run_01.json").read_text())
    assert run["initial_objective"] == 824
    assert (
        run["benchmark"]["problem_snapshot_sha256"]
        == hashlib.sha256((folder / "problem.json").read_bytes()).hexdigest()
    )
    assert run["benchmark"]["knapsack_upper_bound"] == 889
    assert run["validation"]["all_valid"]
    assert run["validation"]["vehicle_ids_preserved"]
    assert run["validation"]["integer_coordinates"]
    assert run["validation"]["objective_matches"]
    assert run["last_state"] is not None
    assert (folder / "run_01_report.png").read_bytes().startswith(b"\x89PNG")
    if algorithm == "simulated_annealing":
        assert (folder / "run_01_diagnostics.png").exists()
        assert run["stagnation_episodes"] == 0
        assert run["configuration"]["parameters"]["evaluation_bias"] == 0
        rows = list(csv.DictReader((folder / "summary.csv").open(newline="")))
        assert int(rows[0]["accepted_candidates"]) == run["accepted_candidates"]
        assert int(rows[0]["stagnation_episodes"]) == 0


def test_adham_configs_use_report_settings():
    hc = load_experiment_config("configs/experiment.hc.adham.json")
    sa = load_experiment_config("configs/experiment.sa.adham.json")
    assert hc.parameters["max_no_improvement"] == 100
    assert sa.parameters["initial_temperature"] == 100
    assert sa.parameters["cooling_rate"] == 0.995
    assert sa.parameters["evaluation_bias"] == 0
    for config in [hc, sa]:
        assert config.runs == 3 and config.random_seed == 42 and config.max_iterations == 1000
        assert config.parameters["plot_style"] == "report"
        assert "reference16" in str(config.output_dir)


def test_report_figures_use_state_geometry_and_recorded_histories():
    plots = import_module("munir.visualization.hc_sa")
    state = State(
        Ship(5, 4, 10), [Vehicle("A", 1, 3, 20, 2, 0, Orientation.VERTICAL, 1, 1)], value=20
    )
    run = ExperimentRun(
        1,
        42,
        0.1234,
        [20, 0, 20],
        20,
        state,
        initial_state=state,
        iterations=2,
        best_objective_history=[20, 20, 20],
        temperature_history=[10, 10, 5],
        acceptance_probability_history=[None, 0.4, 1],
    )
    figure = plots.plot_report_run(run, "simulated_annealing", upper_bound=30)
    left, right, history = figure.axes
    assert left.get_xlim() == (0, 5) and left.get_ylim() == (0, 4)
    assert left.patches[0].get_xy() == (1, 1)
    assert left.patches[0].get_width() == 3 and left.patches[0].get_height() == 1
    assert left.patches[0].get_facecolor() == right.patches[0].get_facecolor()
    assert "State awal" in left.get_title() and "State akhir terbaik" in right.get_title()
    assert list(history.lines[0].get_ydata()) == [20, 0, 20]
    assert list(history.lines[1].get_ydata()) == [20, 20, 20]
    assert list(history.lines[2].get_ydata()) == [30, 30]
    assert "knapsack" in history.lines[2].get_label().lower()
    assert history.get_xlabel() == "Iterasi"
    assert history.get_ylabel() == "ShippingFee (juta rupiah)"
    assert "0.1234" in " ".join(text.get_text() for text in figure.texts)
    diagnostics = plots.plot_diagnostics(run)
    assert list(diagnostics.axes[0].lines[0].get_ydata()) == [0.4, 1]
    assert list(diagnostics.axes[1].lines[0].get_ydata()) == [10, 5]


def test_upper_bound_is_calculated_and_validation_rejects_stale_score():
    helpers = import_module("munir.experiments.hc_sa_metrics")
    assert helpers.weight_upper_bound(load_problem("configs/problem.reference16.json")) == 889
    problem = State(Ship(2, 2, 3), [Vehicle("A", 1, 1, 10, 2, 0), Vehicle("B", 1, 1, 15, 3, 0)])
    assert helpers.weight_upper_bound(problem) == 15
    initial = create_random_initial_state(problem, seed=1)
    invalid_score = State(initial.ship, initial.vehicles, value=999)
    with pytest.raises(ValueError, match="validation"):
        helpers.validate_search_states(problem, initial, invalid_score, initial)


def test_weight_bound_does_not_allocate_by_huge_capacity_when_all_vehicles_fit():
    helpers = import_module("munir.experiments.hc_sa_metrics")
    problem = State(Ship(1, 1, 1_000_000), [Vehicle("A", 1, 1, 10, 1, 0)])
    tracemalloc.start()
    try:
        assert helpers.weight_upper_bound(problem) == 10
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak_bytes < 1_000_000


def test_expensive_optional_knapsack_bound_is_skipped():
    helpers = import_module("munir.experiments.hc_sa_metrics")
    vehicles = [Vehicle(f"V{i}", 1, 1, 10, 20_000, 0) for i in range(24)]
    assert helpers.weight_upper_bound(State(Ship(1, 1, 250_000), vehicles)) is None
