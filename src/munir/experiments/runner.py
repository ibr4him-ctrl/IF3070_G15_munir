import csv
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from munir.algorithms.genetic_algorithm import genetic_algorithm
from munir.algorithms.hill_climbing import stochastic_hill_climbing
from munir.core.initial_state import create_random_initial_state
from munir.core.models import State
from munir.experiments.config import ExperimentConfig


@dataclass(slots=True)
class ExperimentRun:
    run: int
    seed: int
    duration_seconds: float
    objective_history: list[float]
    final_objective: float
    final_state: State
    average_history: list[float] | None = None


@dataclass(slots=True)
class ExperimentResult:
    algorithm: str
    output_directory: Path
    runs: list[ExperimentRun]


def _state_to_dict(state: State) -> dict[str, Any]:
    return {
        "ship": asdict(state.ship),
        "value": state.value,
        "vehicles": [asdict(vehicle) for vehicle in state.vehicles],
    }


def _create_output_directory(base: Path, algorithm: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = base / f"{algorithm}_{timestamp}"
    suffix = 1

    while candidate.exists():
        candidate = base / f"{algorithm}_{timestamp}_{suffix}"
        suffix += 1

    candidate.mkdir(parents=True)
    return candidate


def _run_hill_climbing(problem: State, config: ExperimentConfig, seed: int) -> ExperimentRun:
    initial_state = create_random_initial_state(problem, seed)
    max_no_improvement = int(config.parameters.get("max_no_improvement", 100))

    started = time.perf_counter()
    result = stochastic_hill_climbing(
        initial_state,
        max_iterations=config.max_iterations,
        max_no_improvement=max_no_improvement,
        seed=seed,
    )
    duration = time.perf_counter() - started

    return ExperimentRun(
        run=0,
        seed=seed,
        duration_seconds=duration,
        objective_history=result.objective_history,
        final_objective=result.final_state.value,
        final_state=result.final_state,
    )


def _run_genetic_algorithm(problem: State, config: ExperimentConfig, seed: int) -> ExperimentRun:
    parameters = config.parameters

    started = time.perf_counter()
    result = genetic_algorithm(
        problem,
        population_size=int(parameters.get("population_size", 50)),
        generations=config.max_iterations,
        mutation_rate=float(parameters.get("mutation_rate", 0.1)),
        elitism_count=int(parameters.get("elitism_count", 1)),
        tournament_size=int(parameters.get("tournament_size", 3)),
        seed=seed,
    )
    duration = time.perf_counter() - started

    return ExperimentRun(
        run=0,
        seed=seed,
        duration_seconds=duration,
        objective_history=result.maximum_history,
        average_history=result.average_history,
        final_objective=result.best_state.value,
        final_state=result.best_state,
    )


def _write_run_json(directory: Path, result: ExperimentRun) -> None:
    payload = {
        "run": result.run,
        "seed": result.seed,
        "duration_seconds": result.duration_seconds,
        "final_objective": result.final_objective,
        "objective_history": result.objective_history,
        "average_history": result.average_history,
        "final_state": _state_to_dict(result.final_state),
    }
    path = directory / f"run_{result.run:02d}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_history_csv(directory: Path, runs: list[ExperimentRun]) -> None:
    path = directory / "objective_history.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["run", "seed", "iteration", "objective", "average_objective"],
        )
        writer.writeheader()

        for result in runs:
            for iteration, objective in enumerate(result.objective_history):
                average = None
                if result.average_history is not None:
                    average = result.average_history[iteration]
                writer.writerow(
                    {
                        "run": result.run,
                        "seed": result.seed,
                        "iteration": iteration,
                        "objective": objective,
                        "average_objective": average,
                    }
                )


def run_experiment(problem: State, config: ExperimentConfig) -> ExperimentResult:
    algorithm = config.algorithm.strip().lower()
    runners = {
        "stochastic_hill_climbing": _run_hill_climbing,
        "hill_climbing": _run_hill_climbing,
        "genetic_algorithm": _run_genetic_algorithm,
    }

    if algorithm not in runners:
        supported = ", ".join(sorted(runners))
        raise ValueError(f"Unsupported algorithm: {algorithm}. Choose one of: {supported}")

    base_seed = config.random_seed if config.random_seed is not None else 0
    output_directory = _create_output_directory(config.output_dir, algorithm)
    runs = []

    for run_number in range(1, config.runs + 1):
        seed = base_seed + run_number - 1
        result = runners[algorithm](problem, config, seed)
        result.run = run_number
        runs.append(result)
        _write_run_json(output_directory, result)

    _write_history_csv(output_directory, runs)
    return ExperimentResult(
        algorithm=algorithm,
        output_directory=output_directory,
        runs=runs,
    )
