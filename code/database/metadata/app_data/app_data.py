from abc import ABC
from dataclasses import dataclass, field
from typing import Literal
from database.metadata.metadata import Metadata


# noinspection PyDataclass
@dataclass(kw_only=True)
class AppData(Metadata, ABC):
    app_path: str
    app_name: str
    locale: str

    result_type: Literal["app", "metadata"] = field(default="app")  # discriminator
