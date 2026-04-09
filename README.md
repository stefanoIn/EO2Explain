# EO2Explain

EO2Explain is organized as a layered hazard-analysis pipeline:

- `data/`: raw EO inputs and processed indicator/exposure tables
- `eo_processing/`: Python notebooks for EO indicator and exposure extraction
- `mas/`: Jason reasoning layer, including agents, beliefs, Java internal actions, and MAS config
- `nlp/`: payload transformation, loading, ontology, and report-generation layer
- `outputs/`: raw semantic exports, transformed payloads, and generated reports
- `docs/`: architecture notes and LaTeX report material

## Run The MAS

```bash
cd "/Users/stefanoinfusini/Desktop/SecondYear_MS/SDAI/PROJECT SDAI&NLP/EO2Explain"
./scripts/run_mas.sh
```

## Transform The Jason Payloads

```bash
cd "/Users/stefanoinfusini/Desktop/SecondYear_MS/SDAI/PROJECT SDAI&NLP/EO2Explain"
python3 scripts/run_nlp.py
```

This reads raw JSON from `outputs/semantic_explanations/` and writes cleaned semantic JSON to `outputs/transformed/`.
