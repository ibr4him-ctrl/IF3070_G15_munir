import csv
import json
import time
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from munir.algorithms.genetic_algorithm import genetic_algorithm
from munir.algorithms.hill_climbing import stochastic_hill_climbing
from munir.algorithms.simulated_annealing import simulated_annealing
from munir.core.initial_state import create_random_initial_state
from munir.core.models import State
from munir.experiments.config import ExperimentConfig
from munir.visualization.plots import save_run_plots


@dataclass(slots=True)
class ExperimentRun:
    run: int
    seed: int
    duration_seconds: float
    objective_history: list[float]
    final_objective: float
    final_state: State
    average_history: list[float] | None = None
    initial_state: State | None = None
    iterations: int = 0
    population_size: int | None = None
    last_state: State | None = None
    best_objective_history: list[float] | None = None
    temperature_history: list[float] | None = None
    acceptance_probability_history: list[float | None] | None = None
    delta_history: list[float | None] | None = None
    accepted_history: list[bool | None] | None = None
    no_improvement_history: list[int] | None = None
    non_improving_iterations: int | None = None
    stuck_events: int | None = None
    stop_reason: str | None = None
    configuration: dict[str, Any] | None = None


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

    base.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            candidate = base / f"{algorithm}_{timestamp}_{suffix}"
            suffix += 1


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
        initial_state=result.initial_state,
        iterations=result.iterations,
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
        initial_state=result.initial_best_state,
        iterations=result.generations,
        population_size=result.population_size,
    )


def _run_simulated_annealing(problem: State, config: ExperimentConfig, seed: int) -> ExperimentRun:
    initial = create_random_initial_state(problem, seed)
    parameters = config.parameters
    result = simulated_annealing(
        initial,
        initial_temperature=float(parameters["initial_temperature"]),
        cooling_rate=float(parameters["cooling_rate"]),
        min_temperature=float(parameters["min_temperature"]),
        max_iterations=config.max_iterations,
        seed=seed,
    )
    return ExperimentRun(
        run=0,
        seed=seed,
        duration_seconds=result.duration_seconds,
        objective_history=result.objective_history,
        final_objective=result.final_state.value,
        final_state=result.final_state,
        initial_state=result.initial_state,
        iterations=result.iterations,
        last_state=result.last_state,
        best_objective_history=result.best_objective_history,
        temperature_history=result.temperature_history,
        acceptance_probability_history=result.acceptance_probability_history,
        delta_history=result.delta_history,
        accepted_history=result.accepted_history,
        no_improvement_history=result.no_improvement_history,
        non_improving_iterations=result.non_improving_iterations,
        stuck_events=result.stuck_events,
        stop_reason=result.stop_reason,
    )


def _write_run_json(directory: Path, result: ExperimentRun) -> None:
    # asdict preserves the old state shape and adds the optional metrics above.
    payload = {"schema_version": 2, **asdict(result)}
    path = directory / f"run_{result.run:02d}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_history_csv(directory: Path, runs: list[ExperimentRun]) -> None:
    path = directory / "objective_history.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run",
                "seed",
                "iteration",
                "objective",
                "average_objective",
                "best_objective",
                "temperature",
                "acceptance_probability",
                "delta",
                "accepted",
                "no_improvement",
            ],
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
                        **{
                            name: history[iteration] if history is not None else None
                            for name, history in {
                                "best_objective": result.best_objective_history,
                                "temperature": result.temperature_history,
                                "acceptance_probability": result.acceptance_probability_history,
                                "delta": result.delta_history,
                                "accepted": result.accepted_history,
                                "no_improvement": result.no_improvement_history,
                            }.items()
                        },
                    }
                )


def _write_inputs(directory: Path, problem: State, config: ExperimentConfig) -> None:
    payload = asdict(config)
    payload["output_dir"] = str(config.output_dir)
    (directory / "config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Store a snapshot in the existing loader's format so a run can be replayed.
    problem_payload = {
        "ship": {
            "dimensions": {"w": problem.ship.width, "l": problem.ship.length},
            "max_capacity": problem.ship.max_capacity,
        },
        "vehicles": [
            {
                "id": v.id,
                "dimensions": {"w": v.width, "l": v.length},
                "orientation": v.orientation,
                "shipping_fee": v.shipping_fee,
                "weight": v.weight,
                "eta": v.eta,
                "position": {"x": v.x, "y": v.y},
            }
            for v in problem.vehicles
        ],
    }
    (directory / "problem.json").write_text(json.dumps(problem_payload, indent=2), encoding="utf-8")


def _write_summary(directory: Path, runs: list[ExperimentRun]) -> None:
    fields = [
        "run",
        "seed",
        "initial_objective",
        "final_objective",
        "iterations",
        "duration_seconds",
        "population_size",
        "non_improving_iterations",
        "stuck_events",
    ]
    with (directory / "summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for run in runs:
            writer.writerow(
                {
                    name: run.initial_state.value
                    if name == "initial_objective" and run.initial_state is not None
                    else getattr(run, name, None)
                    for name in fields
                }
            )


def run_experiment(problem: State, config: ExperimentConfig) -> ExperimentResult:
    algorithm = config.algorithm.strip().lower()
    runners = {
        "stochastic_hill_climbing": _run_hill_climbing,
        "hill_climbing": _run_hill_climbing,
        "genetic_algorithm": _run_genetic_algorithm,
        "simulated_annealing": _run_simulated_annealing,
    }

    if algorithm not in runners:
        supported = ", ".join(sorted(runners))
        raise ValueError(f"Unsupported algorithm: {algorithm}. Choose one of: {supported}")

    defaults = {
        "stochastic_hill_climbing": {"max_no_improvement": 100},
        "hill_climbing": {"max_no_improvement": 100},
        "simulated_annealing": {
            "initial_temperature": 100.0,
            "cooling_rate": 0.99,
            "min_temperature": 0.01,
        },
        "genetic_algorithm": {
            "population_size": 50,
            "mutation_rate": 0.1,
            "elitism_count": 1,
            "tournament_size": 3,
        },
    }
    base_seed = config.random_seed if config.random_seed is not None else 0
    config = replace(
        config,
        algorithm=algorithm,
        random_seed=base_seed,
        parameters={**defaults[algorithm], **config.parameters},
    )
    output_directory = _create_output_directory(config.output_dir, algorithm)
    _write_inputs(output_directory, problem, config)
    runs = []

    for run_number in range(1, config.runs + 1):
        seed = base_seed + run_number - 1
        result = runners[algorithm](problem, config, seed)
        result.run = run_number
        result.configuration = {
            "algorithm": algorithm,
            "seed": seed,
            "max_iterations": config.max_iterations,
            "parameters": dict(config.parameters),
        }
        runs.append(result)
        _write_run_json(output_directory, result)
        save_run_plots(result, algorithm, output_directory)

    _write_history_csv(output_directory, runs)
    _write_summary(output_directory, runs)
    return ExperimentResult(
        algorithm=algorithm,
        output_directory=output_directory,
        runs=runs,
    )
