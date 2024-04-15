"""
Abstract Module for common fields of dynamic analysis results between different platforms
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Literal
from database.analysis_results.analysis_result import AnalysisResult


@dataclass(kw_only=True)
class DynamicResult(AnalysisResult, ABC):
    """
    Abstract class for dynamic analysis results
    """

    pcap_path: str
    analysis_log_path: str
    appium_log_path: str

    analysis_type: Literal["static", "dynamic"] = field(default="dynamic")
