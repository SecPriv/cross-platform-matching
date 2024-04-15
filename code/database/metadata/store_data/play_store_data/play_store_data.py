"""
Data class for playstore metadata results.
"""

from dataclasses import dataclass, field
from typing import Literal
from database.metadata.store_data.store_data import StoreData


@dataclass(kw_only=True)
class PlayStoreMetadata(StoreData):
    """
    DTO for the playstore metadata results.
    """

    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "Android",
            "result_type": "metadata"
        }

    # If needed, android store specific fields can be added here

    os: Literal["iOS", "Android"] = field(default="Android")
