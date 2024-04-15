"""
Data class for iOS app store metadata results.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

from database.metadata.store_data.store_data import StoreData


# noinspection PyDataclass
@dataclass(kw_only=True)
class AppStoreData(StoreData):
    """
    DTO for the iOS app store metadata directly fetched from the app store.
    """

    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "iOS",
            "result_type": "metadata"
        }

    app_store_id: str
    # specific attributes extracted from raw_data
    # might need maintenance depending on changes on the App Store
    type: str
    href: str
    attributes: dict
    relationships: dict

    app_extensions: Optional[list] = None
    description: Optional[list] = None

    os: Literal["iOS", "Android"] = field(default="iOS")
