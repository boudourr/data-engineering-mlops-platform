"""
main.py
-------

Entry point of the Automated ETL Pipeline.

Workflow
--------
Raw Data (Bronze)
        │
        ▼
 Automated ETL Pipeline
        │
        ▼
 Clean Data (Silver)
"""

from etl.pipeline import ETLPipeline


def main():
    """
    Execute the complete ETL pipeline.
    """

    pipeline = ETLPipeline()

    pipeline.run()


if __name__ == "__main__":
    main()