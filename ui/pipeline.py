from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eo_processing.flood.flood_indicators import compute_flood_metrics, plot_flood_report_figure
from eo_processing.wildfire.wildfire_indicators import (
    compute_wildfire_metrics,
    plot_wildfire_report_figure,
)
from nlp.generator.report_generator import build_report_text
from nlp.transformer.transform_payload import transform_semantic_explanation


UI_JOBS_DIR = PROJECT_ROOT / "outputs/ui_jobs"
JASON_BIN = os.environ.get("EO2EXPLAIN_JASON_BIN", "jason")
GRADLE_BIN = os.environ.get("EO2EXPLAIN_GRADLE_BIN", "gradle")
MAS_STOP_FILE = ".stop___MAS"


class PipelineError(RuntimeError):
    pass


FLOOD_UPLOAD_KEYS = frozenset({"before_b03", "before_b08", "after_b03", "after_b08"})
WILDFIRE_UPLOAD_KEYS = frozenset(
    {
        "before_b04",
        "before_b08",
        "before_b12",
        "after_b04",
        "after_b08",
        "after_b12",
    }
)


def file_fields_for_hazard(hazard_type: str) -> frozenset[str]:
    if hazard_type == "flood":
        return FLOOD_UPLOAD_KEYS
    if hazard_type == "wildfire":
        return WILDFIRE_UPLOAD_KEYS
    raise PipelineError(f"Unknown hazard_type: {hazard_type!r}")


def uploads_for_hazard(hazard_type: str, files) -> dict[str, object]:
    """Keep only TIFF fields that belong to the selected hazard (ignore the other block)."""
    keys = file_fields_for_hazard(hazard_type)
    return {k: files[k] for k in keys if k in files}


@dataclass
class JobResult:
    job_id: str
    event_id: str
    job_dir: Path
    report_path: Path
    transformed_path: Path
    raw_payload_path: Path
    figure_path: Path | None
    ontology_path: Path | None
    ontology_warning: str | None
    report_text: str


def slugify(value: str) -> str:
    value = value.strip()
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "event"


def bool_token(value: bool) -> str:
    return "true" if value else "false"


def save_upload(upload, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    upload.save(destination)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_jason_log_config(path: Path) -> None:
    content = """handlers=java.util.logging.ConsoleHandler
.level=INFO
java.util.logging.ConsoleHandler.level=INFO
java.util.logging.ConsoleHandler.formatter=java.util.logging.SimpleFormatter
java.util.logging.SimpleFormatter.format=%5$s%n
"""
    write_text(path, content)


def build_mas_command(log_conf_path: Path) -> list[str]:
    gradle_path = shutil.which(GRADLE_BIN)
    if gradle_path:
        return [gradle_path, "run", "--console=plain"]

    jason_path = shutil.which(JASON_BIN)
    if jason_path:
        return [
            jason_path,
            "eo.mas2j",
            "--no-net",
            "--no-mbean",
            "--no-mindinspector",
            "--log-conf",
            str(log_conf_path),
        ]

    raise PipelineError(
        "MAS execution failed: neither 'gradle' nor 'jason' was found in PATH. "
        "Install one of them or set EO2EXPLAIN_GRADLE_BIN / EO2EXPLAIN_JASON_BIN."
    )


def write_events_asl(
    beliefs_dir: Path,
    *,
    event_id: str,
    event_name: str,
    hazard_type: str,
    country_name: str,
    region_name: str,
    timeline_confidence: str,
    late_observation: bool,
    possible_underestimation: bool,
) -> None:
    country_id = slugify(country_name)
    region_id = slugify(region_name)
    content = f"""// Auto-generated for UI job
country_name({country_id}, "{country_name}").
region_name({region_id}, "{region_name}").

event({event_id}).
name({event_id}, "{event_name}").
country({event_id}, {country_id}).
region({event_id}, {region_id}).
event_type({event_id}, {hazard_type}).
timeline_confidence({event_id}, {timeline_confidence}).
late_observation_flag({event_id}, {bool_token(late_observation)}).
possible_underestimation({event_id}, {bool_token(possible_underestimation)}).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
"""
    write_text(beliefs_dir / "events.asl", content)


def write_indicators_asl(
    beliefs_dir: Path,
    *,
    event_id: str,
    hazard_type: str,
    metrics: dict[str, float | int | str],
) -> None:
    if hazard_type == "flood":
        lines = [
            "// Auto-generated for UI job",
            f"mean_ndwi_before({event_id}, {float(metrics['mean_ndwi_before']):.4f}).",
            f"mean_ndwi_after({event_id}, {float(metrics['mean_ndwi_after']):.4f}).",
            f"ndwi_change({event_id}, {float(metrics['ndwi_change']):.4f}).",
            f"water_increase_pct({event_id}, {float(metrics['water_increase_pct_points']):.2f}).",
            f"newly_flooded_area_pct({event_id}, {float(metrics['newly_flooded_area_pct']):.2f}).",
        ]
    else:
        lines = [
            "// Auto-generated for UI job",
            f"mean_ndvi_before({event_id}, {float(metrics['mean_ndvi_before']):.4f}).",
            f"mean_ndvi_after({event_id}, {float(metrics['mean_ndvi_after']):.4f}).",
            f"ndvi_drop({event_id}, {float(metrics['ndvi_drop']):.4f}).",
            f"mean_dnbr({event_id}, {float(metrics['mean_dnbr']):.4f}).",
            f"vegetation_loss_pct({event_id}, {float(metrics['vegetation_loss_pct']):.2f}).",
            f"burned_area_pct({event_id}, {float(metrics['burned_area_pct']):.2f}).",
        ]
    write_text(beliefs_dir / "indicators.asl", "\n".join(lines))


def write_population_asl(beliefs_dir: Path, *, event_id: str, exposure_class: str) -> None:
    content = f"""// Auto-generated for UI job
population_exposure_class({event_id}, {exposure_class}).
"""
    write_text(beliefs_dir / "population_exposure.asl", content)


def write_user_inputs_asl(beliefs_dir: Path, *, event_id: str, user_assessment: str | None) -> None:
    lines = [
        "// Optional user-provided assessments for post-hoc comparison only.",
        "// Auto-generated for UI job",
    ]
    if user_assessment:
        lines.append(f"user_assessment({event_id}, {user_assessment}).")
    write_text(beliefs_dir / "user_inputs.asl", "\n".join(lines))


def prepare_mas_workspace(job_dir: Path) -> Path:
    source_mas = PROJECT_ROOT / "mas"
    target_mas = job_dir / "mas"

    shutil.copytree(source_mas / "agents", target_mas / "agents", dirs_exist_ok=True)
    shutil.copytree(source_mas / "java", target_mas / "java", dirs_exist_ok=True)
    if (source_mas / "config").exists():
        shutil.copytree(source_mas / "config", target_mas / "config", dirs_exist_ok=True)
    shutil.copy2(source_mas / "eo.mas2j", target_mas / "eo.mas2j")
    shutil.copy2(source_mas / "build.gradle", target_mas / "build.gradle")
    shutil.copy2(source_mas / "settings.gradle", target_mas / "settings.gradle")
    beliefs_dir = target_mas / "beliefs"
    beliefs_dir.mkdir(parents=True, exist_ok=True)
    return beliefs_dir


def save_uploaded_event_files(job_dir: Path, hazard_type: str, uploads: dict[str, object]) -> Path:
    event_root = job_dir / "data" / "raw" / ("floods" if hazard_type == "flood" else "wildfires") / "uploaded_event"
    before_name = "before_flooding" if hazard_type == "flood" else "before_wildfire"
    after_name = "after_flooding" if hazard_type == "flood" else "after_wildfire"
    before_dir = event_root / before_name
    after_dir = event_root / after_name

    if hazard_type == "flood":
        mapping = {
            "before_b03": before_dir / "before_B03.tiff",
            "before_b08": before_dir / "before_B08.tiff",
            "after_b03": after_dir / "after_B03.tiff",
            "after_b08": after_dir / "after_B08.tiff",
        }
    else:
        mapping = {
            "before_b04": before_dir / "before_B04.tiff",
            "before_b08": before_dir / "before_B08.tiff",
            "before_b12": before_dir / "before_B12.tiff",
            "after_b04": after_dir / "after_B04.tiff",
            "after_b08": after_dir / "after_B08.tiff",
            "after_b12": after_dir / "after_B12.tiff",
        }

    for field_name, destination in mapping.items():
        upload = uploads.get(field_name)
        if upload is None or not getattr(upload, "filename", ""):
            raise PipelineError(f"Missing required upload: {field_name}")
        save_upload(upload, destination)

    return event_root


def render_figure(job_dir: Path, hazard_type: str, event_name: str, arrays: dict[str, object]) -> Path:
    figures_dir = job_dir / "outputs" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    figure_path = figures_dir / f"{slugify(event_name)}_{hazard_type}.png"
    if hazard_type == "flood":
        figure = plot_flood_report_figure(arrays, event_name)
    else:
        figure = plot_wildfire_report_figure(arrays, event_name)
    figure.savefig(figure_path, dpi=300, bbox_inches="tight")
    try:
        import matplotlib.pyplot as plt

        plt.close(figure)
    except Exception:
        pass
    return figure_path


def newest_stable_json(path: Path) -> Path | None:
    candidates = sorted(path.glob("*.json"))
    if not candidates:
        return None
    latest = candidates[-1]
    try:
        first_size = latest.stat().st_size
    except FileNotFoundError:
        return None
    time.sleep(0.25)
    try:
        second_size = latest.stat().st_size
    except FileNotFoundError:
        return None
    if first_size == second_size and second_size > 0:
        return latest
    return None


def run_mas(job_dir: Path) -> Path:
    mas_dir = job_dir / "mas"
    logs_dir = job_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = logs_dir / "mas_stdout.log"
    stderr_path = logs_dir / "mas_stderr.log"
    log_conf_path = logs_dir / "jason_logging.properties"
    write_jason_log_config(log_conf_path)
    semantic_dir = job_dir / "outputs" / "semantic_explanations"
    semantic_dir.mkdir(parents=True, exist_ok=True)
    command = build_mas_command(log_conf_path)

    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            process = subprocess.Popen(
                command,
                cwd=mas_dir,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
            stable_payload = None
            deadline = time.time() + 120

            while time.time() < deadline:
                stable_payload = newest_stable_json(semantic_dir)
                if stable_payload is not None:
                    (mas_dir / MAS_STOP_FILE).write_text("stop\n", encoding="utf-8")
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    break

                if process.poll() is not None:
                    break

                time.sleep(0.25)

            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    finally:
        stop_file = mas_dir / MAS_STOP_FILE
        if stop_file.exists():
            stop_file.unlink()

    result_code = process.returncode if "process" in locals() else None
    stdout_text = stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else ""

    if result_code not in (0, None):
        stderr = stderr_text.strip() or stdout_text.strip() or "Unknown MAS failure"
        raise PipelineError(f"MAS execution failed: {stderr}")

    raw_file = newest_stable_json(semantic_dir)
    if raw_file is None:
        raise PipelineError("MAS completed without exporting any semantic explanation JSON.")
    return raw_file


def transform_payload(raw_payload_path: Path) -> tuple[dict[str, object], Path]:
    raw = json.loads(raw_payload_path.read_text(encoding="utf-8"))
    transformed = transform_semantic_explanation(raw, raw_payload_path.name)
    transformed_dir = raw_payload_path.parent.parent / "transformed"
    transformed_dir.mkdir(parents=True, exist_ok=True)
    transformed_path = transformed_dir / raw_payload_path.name
    transformed_path.write_text(
        json.dumps(transformed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return transformed, transformed_path


def maybe_populate_ontology(job_dir: Path) -> tuple[Path | None, str | None]:
    ontology_path = job_dir / "outputs" / "ontology" / "eo2explain_populated.rdf"
    ontology_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "nlp/ontology/populate_ontology.py"),
            "--payload-dir",
            str(job_dir / "outputs" / "transformed"),
            "--output",
            str(ontology_path),
            "--ontology",
            str(PROJECT_ROOT / "nlp/ontology/eo2explain.rdf"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "Ontology population failed."
        return None, warning
    return ontology_path, None


def run_job(form: dict[str, str], files: dict[str, object]) -> JobResult:
    hazard_type = form["hazard_type"]
    if hazard_type not in ("flood", "wildfire"):
        raise PipelineError("hazard_type must be flood or wildfire.")
    event_name = form["event_name"].strip()
    if not event_name:
        raise PipelineError("Event name is required.")

    event_id = slugify(form.get("event_id", "") or event_name)
    job_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    job_dir = UI_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    uploads = uploads_for_hazard(hazard_type, files)
    event_dir = save_uploaded_event_files(job_dir, hazard_type, uploads)
    beliefs_dir = prepare_mas_workspace(job_dir)

    if hazard_type == "flood":
        metrics, arrays = compute_flood_metrics(event_dir)
    else:
        metrics, arrays = compute_wildfire_metrics(event_dir)

    figure_path = render_figure(job_dir, hazard_type, event_name, arrays)

    write_events_asl(
        beliefs_dir,
        event_id=event_id,
        event_name=event_name,
        hazard_type=hazard_type,
        country_name=form["country_name"].strip(),
        region_name=form["region_name"].strip(),
        timeline_confidence=form["timeline_confidence"],
        late_observation=form.get("late_observation") == "on",
        possible_underestimation=form.get("possible_underestimation") == "on",
    )
    write_indicators_asl(
        beliefs_dir,
        event_id=event_id,
        hazard_type=hazard_type,
        metrics=metrics,
    )
    write_population_asl(
        beliefs_dir,
        event_id=event_id,
        exposure_class=form["population_exposure_class"],
    )
    user_assessment = form.get("user_assessment", "").strip() or None
    if user_assessment == "none":
        user_assessment = None
    write_user_inputs_asl(
        beliefs_dir,
        event_id=event_id,
        user_assessment=user_assessment,
    )

    raw_payload_path = run_mas(job_dir)
    transformed_payload, transformed_path = transform_payload(raw_payload_path)

    reports_dir = job_dir / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_text = build_report_text(transformed_payload)
    report_path = reports_dir / f"{event_id}.txt"
    report_path.write_text(report_text, encoding="utf-8")

    ontology_path, ontology_warning = maybe_populate_ontology(job_dir)
    if ontology_warning:
        write_text(job_dir / "logs" / "ontology_warning.txt", ontology_warning)

    return JobResult(
        job_id=job_id,
        event_id=event_id,
        job_dir=job_dir,
        report_path=report_path,
        transformed_path=transformed_path,
        raw_payload_path=raw_payload_path,
        figure_path=figure_path,
        ontology_path=ontology_path,
        ontology_warning=ontology_warning,
        report_text=report_text,
    )
