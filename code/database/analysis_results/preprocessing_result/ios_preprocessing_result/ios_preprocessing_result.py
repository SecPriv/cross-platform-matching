from dataclasses import dataclass, field
from typing import Literal, Optional

from database.analysis_results.preprocessing_result.ios_preprocessing_result.entitlements.entitlements import Entitlements
from database.analysis_results.preprocessing_result.preprocessing_result import PreprocessingResult
from database.analysis_results.preprocessing_result.ios_preprocessing_result.plist.plist import Plist


@dataclass(kw_only=True)
class iOSPreprocessingResult(PreprocessingResult):

    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "iOS",
            "analysis_type": "preprocessing"
        }

    os: Literal["iOS", "Android"] = field(default="iOS")
    entitlements: Optional[dict] = None
    plist: Optional[dict] = None
    metadata: Optional[object] = None
    certificates: Optional[object] = None
    frameworks: Optional[list] = None
