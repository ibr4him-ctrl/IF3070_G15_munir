import csv
import json
import subprocess
import sys
from dataclasses import asdict

import pytest

from munir.core.constraints import is_valid_state
from munir.core.models import Ship, State, Vehicle
from munir.experiments.config import ExperimentConfig
from munir.experiments.runner import run_experiment
from munir.io.json_loader import load_experiment_config, load_problem


@pytest.mark.parametrize(
    "algorithm",
    [
        "stochastic_hill_climbing",
        "simulated_annealing",
        "genetic_algorithm",
    ],
)
def test_runner_exports_real_results_config_states_metrics_and_plots(tmp_path, algorithm):
    problem = State(Ship(2, 2, 5), [Vehicle("A", 1, 2, 30, 3, 0), Vehicle("B", 2, 2, 50, 4, 1)])
    config = ExperimentConfig(
        algorithm,
        runs=2,
        max_iterations=4,
        random_seed=41,
        output_dir=tmp_path,
        parameters={"population_size": 4} if algorithm == "genetic_algorithm" else {},
    )
    result = run_experiment(problem, config)
    folder = result.output_directory
    assert [run.seed for run in result.runs] == [41, 42]
    assert load_problem(folder / "problem.json") == problem
    saved_config = load_experiment_config(folder / "config.json")
    assert saved_config.algorithm == algorithm
    assert saved_config.random_seed == 41
    if algorithm == "simulated_annealing":
        assert saved_config.parameters["initial_temperature"] == 100
    rows = list(csv.DictReader((folder / "objective_history.csv").open(newline="")))
    assert len(rows) == sum(run.iterations + 1 for run in result.runs)
    for run in result.runs:
        data = json.loads((folder / f"run_{run.run:02d}.json").read_text())
        assert data["initial_state"] == json.loads(json.dumps(asdict(run.initial_state)))
        assert data["final_state"]["value"] == run.final_objective
        assert data["iterations"] == len(run.objective_history) - 1
        assert data["configuration"]["seed"] == run.seed
        assert data["objective_history"] == run.objective_history
        assert is_valid_state(run.final_state)
        run_rows = [row for row in rows if int(row["run"]) == run.run]
        assert [float(row["objective"]) for row in run_rows] == run.objective_history
        kinds = ["initial", "final", "objective"]
        if algorithm == "simulated_annealing":
            kinds.append("annealing")
            assert run_rows[0]["acceptance_probability"] == ""
            assert [float(row["temperature"]) for row in run_rows] == run.temperature_history
            assert data["final_objective"] == max(data["objective_history"])
        if algorithm == "genetic_algorithm":
            assert data["population_size"] == 4
            assert [float(row["average_objective"]) for row in run_rows] == run.average_history
        for kind in kinds:
            image = folder / f"run_{run.run:02d}_{kind}.png"
            assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            assert image.stat().st_size > 1000
    assert (folder / "summary.csv").exists()


def test_repeated_runner_preserves_old_outputs_and_reproduces_search(tmp_path):
    problem = State(Ship(2, 2, 5), [Vehicle("A", 1, 2, 30, 3, 0)])
    config = ExperimentConfig(
        "simulated_annealing", runs=1, max_iterations=5, random_seed=9, output_dir=tmp_path
    )
    first = run_experiment(problem, config)
    original_bytes = (first.output_directory / "run_01.json").read_bytes()
    second = run_experiment(problem, config)
    assert first.output_directory != second.output_directory
    assert (first.output_directory / "run_01.json").read_bytes() == original_bytes
    assert first.runs[0].objective_history == second.runs[0].objective_history
    assert first.runs[0].final_state == second.runs[0].final_state


def test_interface_cli_runs_supplied_config(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "algorithm": "simulated_annealing",
                "runs": 1,
                "max_iterations": 2,
                "random_seed": 2,
                "output_dir": str(tmp_path / "results"),
            }
        )
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "munir.interface",
            "--problem",
            "configs/problem.example.json",
            "--config",
            str(config),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "simulated_annealing" in completed.stdout
    assert len(list((tmp_path / "results").glob("*/run_01.json"))) == 1
