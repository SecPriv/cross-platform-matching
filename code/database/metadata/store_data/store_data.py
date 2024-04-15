from abc import ABC
from dataclasses import dataclass, field
from typing import Literal
from database.metadata.metadata import Metadata


# noinspection PyDataclass
@dataclass(kw_only=True)
class StoreData(Metadata, ABC):
    path: str
    raw_data: dict
    version: str
    user_ratings: int
    price: float

    result_type: Literal["app", "metadata"] = field(default="metadata")  # discriminator
