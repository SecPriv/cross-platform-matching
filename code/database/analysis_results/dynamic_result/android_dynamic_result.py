from dataclasses import dataclass, field
from typing import Literal
from database.analysis_results.dynamic_result.dynamic_result import DynamicResult


@dataclass(kw_only=True)
class AndroidDynamicResult(DynamicResult):
    """
    Abstract class for static analysis results
    """

    os: Literal["ios", "android"] = field(default="android")
