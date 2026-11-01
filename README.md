# Modern Data Engineering Platform

A Streamlit application for moving tabular data through ETL, warehouse,
profiling, monitoring, BI preparation, and MLOps workflows.

## Quick start

Create and activate a virtual environment, then install the project runtime
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install streamlit pandas numpy scikit-learn joblib pyarrow openpyxl
```

Start the application from the project root:

```powershell
streamlit run app/Command_Center.py
```

## Recommended workflow

1. Upload a dataset in **Data Upload**.
2. Run **ETL** to create the Silver layer.
3. Build the warehouse in **Warehouse**.
4. In **MLOps**, choose a meaningful target and run model training.
5. Review artifacts, predictions, and monitoring results.

MLOps rejects ID-like or free-text classification targets with excessive
cardinality. This prevents unsafe memory allocations. Use a business category
or numeric measure as the target instead.

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
