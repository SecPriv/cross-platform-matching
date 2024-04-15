"""
Module managing android app entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from database.metadata.app_data.app_data import AppData


# noinspection PyDataclass
@dataclass(kw_only=True)
class AndroidApp(AppData):
    """
    An android app data object manages android apps.
    """

    @staticmethod
    def _get_discriminator() -> dict:
        return {
            "os": "Android",
            "result_type": "app"
        }

    # Android specific app information can be added below
    gsfid: str  # Integer that identifies the account that was used for downloading

    os: Literal["iOS", "Android"] = field(default="Android")


if __name__ == '__main__':
    print("Total android apps currently in the DB:")
    print(AndroidApp.collection().count_documents({}))
