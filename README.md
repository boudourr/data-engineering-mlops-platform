# Data Engineering & MLOps Platform

An end-to-end Streamlit platform for turning tabular data into reliable
analytics and machine-learning workflows. The project combines data
ingestion, ETL, profiling, warehouse generation, interactive dashboards,
monitoring, and MLOps in one application.

## Features

- Upload and inspect tabular datasets.
- Transform raw data into validated Silver and Gold layers.
- Infer warehouse schemas and generate analytical tables.
- Profile datasets with reusable notebooks and reports.
- Generate interactive KPIs and charts for business analysis.
- Train, evaluate, and use machine-learning models.
- Keep each experiment isolated with run-specific artifacts.

## Architecture

```text
Data upload
    ↓
ETL: extract → transform → validate → load
    ↓
Warehouse and profiling
    ↓
BI dashboards and monitoring
    ↓
MLOps: train → evaluate → predict
```

Key directories:

| Directory | Purpose |
| --- | --- |
| `app/` | Streamlit command center and user interface |
| `etl/` | Extraction, transformation, validation, and loading |
| `warehouse/` | Schema inference and warehouse generation |
| `profiling/` | Dataset profiling utilities |
| `mlops/` | Training, evaluation, and prediction pipelines |
| `monitoring/` | Data and model monitoring |
| `documentation/`, `notebooks/` | Exploration and technical documentation |
| `tests/` | Automated reliability checks |

## Installation

Create and activate a virtual environment, then install the runtime
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install streamlit pandas numpy scikit-learn joblib pyarrow openpyxl plotly
```

## Run the application

From the project root:

```powershell
streamlit run app/Command_Center.py
```

Recommended workflow:

1. Open **Data Upload** and upload a dataset.
2. Run **ETL** to create the Silver layer.
3. Build the warehouse.
4. Open **MLOps**, select a meaningful target, and train a model.
5. Review predictions, dashboards, and monitoring results.

MLOps rejects ID-like or free-text classification targets with excessive
cardinality to prevent unsafe memory allocations. Use a business category or
numeric measure as the target instead.

## Verification

Run the automated reliability checks:

```powershell
python -m unittest discover -s tests -v
```

Run a syntax check across the core modules:

```powershell
python -m compileall -q app etl mlops monitoring profiling warehouse
```

## Runtime artifacts

Each user run is isolated under `data/runs/<run_id>`. MLOps artifacts are
stored under `models/<run_id>` and `predictions/<run_id>`, allowing multiple
experiments to coexist without overwriting one another.

Datasets, logs, trained model binaries, generated reports, Power BI files, and
other large runtime outputs are excluded from Git through `.gitignore`.
Provide your own data through the application when running the project locally.
