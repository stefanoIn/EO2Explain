# EO2Explain

EO2Explain is organized as a layered hazard-analysis pipeline:

- `data/`: raw EO inputs and processed indicator/exposure tables
- `eo_processing/`: Python notebooks for EO indicator and exposure extraction
- `mas/`: Jason reasoning layer, including agents, beliefs, Java internal actions, and MAS config
- `nlp/`: payload transformation, loading, ontology, and report-generation layer
- `outputs/`: transformed payloads and generated reports
- `docs/`: architecture notes and LaTeX report material

## Requirements

### Core requirements

The default project run starts from the precomputed indicator and exposure CSV files already stored in `data/processed/`. To run that pipeline, the following are required:

- Python `3.10+`
- Java JDK `17+`

Python packages required by the default run:

- `owlready2`
- `flask`
- `markupsafe`

### Additional Python packages for EO recomputation

If `--with-eo` is used, the EO preprocessing stage also requires:

- `numpy`
- `rasterio`
- `matplotlib`
- `pyproj`
- `shapely`

### MAS requirements

The reasoning layer is a Jason multi-agent system with custom Java internal actions. The MAS project depends on:

- `io.github.jason-lang:jason-interpreter:3.3.0`

The repository now includes a Gradle wrapper for the MAS project:

- `mas/gradlew`
- `mas/gradlew.bat`

This is the primary MAS launch path used by `scripts/run_project.py`. A Jason CLI installation in `PATH` is still supported as a fallback, but it is no longer required for the default project run.

### Platform notes

- macOS/Linux: run from a normal shell
- Windows: the wrapper uses `gradlew.bat` through `cmd /c`, so the same project entrypoint can be used without a Git-Bash-only requirement

## Single-Command Run

For hand-in and reproducibility, the project can be executed from a single entrypoint:

```bash
cd EO2Explain
python3 scripts/run_project.py
```

This default path starts from the precomputed EO indicator and exposure CSV files already stored in `data/processed/`. It then:

- generates the Jason belief files
- runs the MAS
- transforms the semantic payloads
- populates and validates the ontology
- generates the final reports

The main generated artifacts are written to:

- `outputs/reports/`
- `outputs/transformed/`
- `nlp/ontology/eo2explain_populated.rdf`

If full EO recomputation is needed, including the indicator-extraction stage, run:

```bash
cd EO2Explain
python3 scripts/run_project.py --with-eo
```

This optional mode requires the raw EO inputs.

If old generated artifacts should be removed before the run, add:

```bash
cd EO2Explain
python3 scripts/run_project.py --clean
```

## Run The UI Only

To launch the local web UI without running the full repository pipeline first:

```bash
cd EO2Explain
python3 scripts/run_ui.py
```

By default, the UI starts on:

- `http://127.0.0.1:8000`

The UI lets you upload a single flood or wildfire event, then runs the EO, MAS, transformation, ontology, and report-generation steps for that uploaded case inside a per-job workspace under `ui/jobs/`.

Optional flags:

```bash
cd EO2Explain
python3 scripts/run_ui.py --host 0.0.0.0 --port 8000 --debug
```

- `--host`: bind address, default `127.0.0.1`
- `--port`: bind port, default `8000`
- `--debug`: enable Flask debug mode

Running the UI still requires the same runtime stack used by the interactive pipeline:

- Python `3.10+`
- Java JDK `17+`
- Python packages `flask`, `markupsafe`, and `owlready2`
- EO packages such as `numpy`, `rasterio`, `matplotlib`, `pyproj`, and `shapely` if you want the uploaded-event EO processing step to run successfully

Generated UI job artifacts are written under:

- `ui/jobs/`

## Run The MAS Only

```bash
cd EO2Explain
./scripts/run_mas.sh
```

The Jason CLI runs the MAS from `mas/`, using `mas/eo.mas2j`.
Raw Jason semantic exports are written to `mas/outputs/semantic_explanations/`.

## Transform The Jason Payloads Only

```bash
cd EO2Explain
python3 scripts/run_nlp.py
```

This reads raw JSON from `mas/outputs/semantic_explanations/` and writes cleaned semantic JSON to `outputs/transformed/`.
It also populates the Protégé ontology and writes the result to `nlp/ontology/eo2explain_populated.rdf`.
