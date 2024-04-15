from dataclasses import dataclass, field
from typing import Literal, Optional

from database.analysis_results.preprocessing_result.preprocessing_result import PreprocessingResult


@dataclass(kw_only=True)
class AndroidPreprocessingResult(PreprocessingResult):
    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "Android",
            "analysis_type": "static"
        }

    os: Literal["iOS", "Android"] = field(default="Android")
    apk_info: Optional[dict] = None
    frameworks: Optional[list[dict]] = None
    certificates: Optional[list[dict]] = None
    metadata: Optional[object] = None