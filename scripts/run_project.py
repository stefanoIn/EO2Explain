#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FLOOD_DIR = PROJECT_ROOT / "data/raw/floods"
RAW_WILDFIRE_DIR = PROJECT_ROOT / "data/raw/wildfires"
FLOOD_CSV = PROJECT_ROOT / "data/processed/indicators/flood_eo_indicators_summary.csv"
WILDFIRE_CSV = PROJECT_ROOT / "data/processed/indicators/wildfire_eo_indicators_summary.csv"
POPULATION_CSV = PROJECT_ROOT / "data/processed/exposure/population_exposure_summary.csv"
INDICATORS_ASL = PROJECT_ROOT / "mas/beliefs/indicators.asl"
POPULATION_ASL = PROJECT_ROOT / "mas/beliefs/population_exposure.asl"
SEMANTIC_DIR = PROJECT_ROOT / "outputs/semantic_explanations"
TRANSFORMED_DIR = PROJECT_ROOT / "outputs/transformed"
REPORTS_DIR = PROJECT_ROOT / "outputs/reports"
ONTOLOGY_PATH = PROJECT_ROOT / "nlp/ontology/eo2explain_populated.rdf"
SUPPRESSED_OUTPUT_SNIPPETS = (
    "SQLite3 version 3.40.0 and 3.41.2 have huge performance regressions",
)


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def print_stage(title: str, details: list[str]) -> None:
    print(f"\n==> {title}")
    for line in details:
        print(f"    {line}")


def count_json_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.json")))


def filter_output(text: str | None) -> str:
    if not text:
        return ""
    kept_lines: list[str] = []
    for line in text.splitlines():
        if any(snippet in line for snippet in SUPPRESSED_OUTPUT_SNIPPETS):
            continue
        kept_lines.append(line)
    if not kept_lines:
        return ""
    filtered = "\n".join(kept_lines)
    if text.endswith("\n"):
        filtered += "\n"
    return filtered


def run_step(command: list[str], cwd: Path) -> None:
    print(f"    command: {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    stdout = filter_output(completed.stdout)
    stderr = filter_output(completed.stderr)
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def available_mas_commands() -> list[tuple[list[str], Path]]:
    commands: list[tuple[list[str], Path]] = []
    mas_dir = PROJECT_ROOT / "mas"
    is_windows = os.name == "nt"

    if is_windows:
        for executable in ("jason.bat", "jason.cmd", "jason.exe", "jason"):
            jason = shutil.which(executable)
            if jason:
                commands.append(([jason, "eo.mas2j"], mas_dir))
                break
    else:
        jason = shutil.which("jason")
        if jason:
            commands.append(([jason, "eo.mas2j"], mas_dir))

    if is_windows:
        gradlew = mas_dir / "gradlew.bat"
        if gradlew.exists():
            commands.append((["cmd", "/c", str(gradlew), "run", "--console=plain"], mas_dir))
    else:
        gradlew = mas_dir / "gradlew"
        if gradlew.exists():
            commands.append(([str(gradlew), "run", "--console=plain"], mas_dir))

    gradle = shutil.which("gradle")
    if gradle:
        commands.append(([gradle, "run", "--console=plain"], mas_dir))

    return commands


def run_mas() -> None:
    commands = available_mas_commands()
    if not commands:
        raise SystemExit(
            "No MAS runner was found. Install Gradle or the Jason CLI, then rerun this script."
        )

    failures: list[str] = []
    before_count = count_json_files(SEMANTIC_DIR)
    for command, cwd in commands:
        print_stage(
            "Run the multi-agent system",
            [
                "launching Jason from mas/eo.mas2j",
                f"semantic payloads will be written to {rel(SEMANTIC_DIR)}",
                (
                    "if a Jason GUI window appears, that is the runtime console; "
                    "the actual MAS output is the exported JSON files"
                ),
                f"runner: {' '.join(command)}",
            ],
        )
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        stdout = filter_output(completed.stdout)
        stderr = filter_output(completed.stderr)
        if stdout:
            print(stdout, end="" if stdout.endswith("\n") else "\n")
        if stderr:
            print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
        if completed.returncode == 0:
            after_count = count_json_files(SEMANTIC_DIR)
            print(f"    MAS completed. Semantic payload files available: {after_count} (was {before_count}).")
            return
        failure_detail = f"{' '.join(command)} (exit code {completed.returncode})"
        if stderr:
            failure_detail = f"{failure_detail}\n{stderr.strip()}"
        failures.append(failure_detail)
        print("    MAS runner failed, trying the next available option.")

    raise SystemExit(
        "All MAS runners failed:\n- " + "\n- ".join(failures)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the EO2Explain pipeline with a single command. "
            "By default it starts from the precomputed indicator CSV files."
        )
    )
    parser.add_argument(
        "--with-eo",
        action="store_true",
        help="Recompute EO indicators and exposure before generating beliefs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.with_eo:
        print_stage(
            "EO preprocessing",
            [
                f"reading raw flood TIFFs from {rel(RAW_FLOOD_DIR)}",
                f"reading raw wildfire TIFFs from {rel(RAW_WILDFIRE_DIR)}",
                f"writing flood indicator summary to {rel(FLOOD_CSV)}",
                f"writing wildfire indicator summary to {rel(WILDFIRE_CSV)}",
                f"writing population exposure summary to {rel(POPULATION_CSV)}",
            ],
        )
        run_step(
            [sys.executable, "scripts/run_eo_processing.py"],
            PROJECT_ROOT,
        )

    print_stage(
        "Generate Jason belief files from processed indicators",
        [
            f"reading flood indicators from {rel(FLOOD_CSV)}",
            f"reading wildfire indicators from {rel(WILDFIRE_CSV)}",
            f"reading exposure summary from {rel(POPULATION_CSV)}",
            f"writing hazard indicator beliefs to {rel(INDICATORS_ASL)}",
            f"writing exposure beliefs to {rel(POPULATION_ASL)}",
        ],
    )
    run_step(
        [sys.executable, "scripts/generate_indicator_beliefs.py"],
        PROJECT_ROOT,
    )

    run_mas()

    print_stage(
        "Run transformation, ontology, and report generation",
        [
            f"reading semantic payloads from {rel(SEMANTIC_DIR)}",
            f"writing transformed payloads to {rel(TRANSFORMED_DIR)}",
            f"writing populated ontology to {rel(ONTOLOGY_PATH)}",
            f"writing reports to {rel(REPORTS_DIR)}",
        ],
    )
    run_step(
        [sys.executable, "scripts/run_nlp.py"],
        PROJECT_ROOT,
    )

    print("\nPipeline completed.")
    print(f"Reports: {rel(REPORTS_DIR)}")
    print(f"Transformed payloads: {rel(TRANSFORMED_DIR)}")
    print(f"Semantic payloads: {rel(SEMANTIC_DIR)}")
    print(f"Populated ontology: {rel(ONTOLOGY_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
