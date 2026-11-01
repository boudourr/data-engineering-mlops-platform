"""
===========================================================
Profiling Framework
-----------------------------------------------------------
Author : Boudour Mdallel
Project : Modern Data Engineering Platform

Description:
Initialization file for the Profiling Framework.
Exports the main profiling classes.
===========================================================
"""

from .profiler import DataProfiler
from .statistics import StatisticsAnalyzer
from .quality import DataQualityAnalyzer
from .frequency import FrequencyAnalyzer
from .outliers import OutlierAnalyzer
from .integrity import IntegrityAnalyzer
from .reports import ReportGenerator

__all__ = [
    "DataProfiler",
    "StatisticsAnalyzer",
    "DataQualityAnalyzer",
    "FrequencyAnalyzer",
    "OutlierAnalyzer",
    "IntegrityAnalyzer",
    "ReportGenerator",
]