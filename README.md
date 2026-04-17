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
- Jason CLI available in `PATH`

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

In practice, the easiest supported path is to have the Jason CLI installed and callable from the shell used to launch the project.

### Platform notes

- macOS/Linux: run from a normal shell
- Windows: run from `Git Bash`

Windows support should be understood as Git-Bash-based execution of the MAS launcher, not as guaranteed native `cmd.exe` or PowerShell support.

## Single-Command Run

For hand-in and reproducibility, the project can be executed from a single entrypoint:

```bash
cd EO2Explain
python3 scripts/run_project.py
```

On Windows, the same command should be launched from `Git Bash`. If the local Python installation is exposed as `python` rather than `python3`, the command can be adapted accordingly.

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
