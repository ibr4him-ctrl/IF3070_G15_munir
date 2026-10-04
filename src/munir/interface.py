from pathlib import Path

from munir.experiments.runner import ExperimentResult, run_experiment
from munir.io.json_loader import load_experiment_config, load_problem


def run_from_files(
    problem_path: str | Path,
    config_path: str | Path,
) -> ExperimentResult:
    problem = load_problem(problem_path)
    config = load_experiment_config(config_path)
    return run_experiment(problem, config)
