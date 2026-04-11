from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask, abort, redirect, render_template, request, send_file, url_for

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.pipeline import JobResult, PipelineError, UI_JOBS_DIR, run_job


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/analyze")
    def analyze():
        try:
            result = run_job(request.form, request.files)
        except PipelineError as exc:
            return render_template("index.html", error=str(exc), form=request.form), 400
        return redirect(url_for("job_result", job_id=result.job_id))

    @app.get("/jobs/<job_id>")
    def job_result(job_id: str):
        job_dir = UI_JOBS_DIR / job_id
        if not job_dir.exists():
            abort(404)

        reports = sorted((job_dir / "outputs" / "reports").glob("*.txt"))
        transformed = sorted((job_dir / "outputs" / "transformed").glob("*.json"))
        semantic = sorted((job_dir / "outputs" / "semantic_explanations").glob("*.json"))
        ontology = sorted((job_dir / "outputs" / "ontology").glob("*.rdf"))

        if not reports:
            abort(404)

        ontology_warning = None
        ontology_warning_summary = None
        warning_path = job_dir / "logs" / "ontology_warning.txt"
        if warning_path.exists():
            ontology_warning = warning_path.read_text(encoding="utf-8")
            if "No module named 'owlready2'" in ontology_warning:
                ontology_warning_summary = (
                    "Ontology population was skipped because owlready2 is not installed "
                    "in the Python interpreter used by the UI."
                )
            else:
                ontology_warning_summary = "Ontology population did not complete."

        mas_stdout_path = job_dir / "logs" / "mas_stdout.log"
        mas_stderr_path = job_dir / "logs" / "mas_stderr.log"
        mas_stdout = mas_stdout_path.read_text(encoding="utf-8").strip() if mas_stdout_path.exists() else None
        mas_stderr = mas_stderr_path.read_text(encoding="utf-8").strip() if mas_stderr_path.exists() else None

        report_raw = reports[0].read_text(encoding="utf-8")
        return render_template(
            "result.html",
            job_id=job_id,
            report_raw=report_raw,
            report_path=reports[0],
            transformed_path=transformed[0] if transformed else None,
            semantic_path=semantic[0] if semantic else None,
            ontology_path=ontology[0] if ontology else None,
            ontology_warning=ontology_warning,
            ontology_warning_summary=ontology_warning_summary,
            mas_stdout=mas_stdout,
            mas_stderr=mas_stderr,
        )

    @app.get("/jobs/<job_id>/artifact/<artifact>")
    def artifact(job_id: str, artifact: str):
        job_dir = UI_JOBS_DIR / job_id
        mapping = {
            "report": next((job_dir / "outputs" / "reports").glob("*.txt"), None),
            "transformed": next((job_dir / "outputs" / "transformed").glob("*.json"), None),
            "semantic": next((job_dir / "outputs" / "semantic_explanations").glob("*.json"), None),
            "figure": next((job_dir / "outputs" / "figures").glob("*.png"), None),
            "ontology": next((job_dir / "outputs" / "ontology").glob("*.rdf"), None),
            "mas_stdout": job_dir / "logs" / "mas_stdout.log",
            "mas_stderr": job_dir / "logs" / "mas_stderr.log",
        }
        path = mapping.get(artifact)
        if path is None or not path.exists():
            abort(404)
        return send_file(path)

    return app


app = create_app()
