"""
Module managing iOS app entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from database.metadata.app_data.app_data import AppData


# noinspection PyDataclass
@dataclass(kw_only=True)
class iOSApp(AppData):
    """
    An iOS app data object manages data specific to iOS apps.
    """

    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "iOS",
            "result_type": "app"
        }

    app_store_id: str
    apple_id_email: str
    dumped_path: str
    dumped_hash: str

    os: Literal["iOS", "Android"] = field(default="iOS")
