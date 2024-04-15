"""
Data class for iOS dynamic analysis results.
"""

from dataclasses import dataclass, field
from typing import Dict, Literal
from database.analysis_results.ios_result.ios_result import iOSResult


# In order to store additional fields for a result, you can extend the
# "PipelineResult" base-class. Then....
# noinspection PyDataclass
@dataclass(kw_only=True)
class iOSDynamicResult(iOSResult):
    """
    DTO for the dynamic iOS analysis results.
    """

    # ...hard-code the "defaults" for certain fields from iOSResult...
    analysis_type: Literal["dynamic"] = field(default="dynamic")

    # ...and finally add additional properties here that are specific for all iOS static analysis results.
    result_type: Literal["analysis-result", "app-store-info", "log"] = field(
        default="analysis-result"
    )
    app_info: Dict
    access_types: Dict
