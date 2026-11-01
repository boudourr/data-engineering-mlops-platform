"""
===========================================================
Report Generator
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Exports profiling results into multiple formats:
- CSV
- Excel
- Markdown
- HTML
===========================================================
"""

import os
import pandas as pd


class ReportGenerator:

    def __init__(self, output_folder="reports"):

        self.output_folder = output_folder

        os.makedirs(self.output_folder, exist_ok=True)

    # =====================================================
    # Export CSV
    # =====================================================

    def to_csv(self, dataframe, filename):

        path = os.path.join(
            self.output_folder,
            filename + ".csv"
        )

        dataframe.to_csv(path, index=False)

        return path

    # =====================================================
    # Export Excel
    # =====================================================

    def to_excel(self, dataframe, filename):

        path = os.path.join(
            self.output_folder,
            filename + ".xlsx"
        )

        dataframe.to_excel(path, index=False)

        return path

    # =====================================================
    # Export HTML
    # =====================================================

    def to_html(self, dataframe, filename):

        path = os.path.join(
            self.output_folder,
            filename + ".html"
        )

        dataframe.to_html(path, index=False)

        return path

    # =====================================================
    # Export Markdown
    # =====================================================

    def to_markdown(self, dataframe, filename):

        path = os.path.join(
            self.output_folder,
            filename + ".md"
        )

        with open(path, "w", encoding="utf-8") as file:

            try:
                    file.write(dataframe.to_markdown(index=False))
            except ImportError:
                    print("Warning: 'tabulate' is not installed. Markdown report was skipped.")

        return path

    # =====================================================
    # Export Multiple Reports
    # =====================================================

    def export_all(self, reports: dict):

        exported = {}

        for name, report in reports.items():

            if isinstance(report, pd.DataFrame):

                exported[name] = {

                    "csv": self.to_csv(report, name),

                    "excel": self.to_excel(report, name),

                    "html": self.to_html(report, name),

                    "markdown": self.to_markdown(report, name)

                }

        return exported