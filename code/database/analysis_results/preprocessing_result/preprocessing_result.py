
from dataclasses import dataclass, field
from typing import Literal, Optional

from database.analysis_results.analysis_result import AnalysisResult

@dataclass(kw_only=True)
class PreprocessingResult(AnalysisResult):

    analysis_type: Literal['preprocessing', 'dynamic'] = field(default='preprocessing')
    icon: Optional[object] = None