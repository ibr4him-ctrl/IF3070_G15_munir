import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Jalankan eksperimen penempatan kendaraan Munir")
    parser.add_argument("--problem", required=True, type=Path, help="File JSON persoalan")
    parser.add_argument(
        "--config", required=True, type=Path, help="File JSON konfigurasi eksperimen"
    )
    args = parser.parse_args()
    try:
        result = run_from_files(args.problem, args.config)
    except ValueError as error:
        parser.error(str(error))
    print(f"{result.algorithm}: {result.output_directory}")
    for run in result.runs:
        print(
            f"Run {run.run}: seed={run.seed}, objective={run.final_objective:g}, "
            f"iterations={run.iterations}, duration={run.duration_seconds:.4f}s"
        )


if __name__ == "__main__":
    main()
