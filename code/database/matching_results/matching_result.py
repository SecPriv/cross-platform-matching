from dataclasses import dataclass
from typing import Optional

from bson import ObjectId

import database.db_connector as db_connector

@dataclass(kw_only=True)
class MatchingResult:
    _id: Optional[ObjectId] = None
    ios_id: str
    android_id: str
    scores: dict[str, float]
    weighted_score: Optional[float]
    average_score: float
    linear_score: Optional[float]

    @staticmethod
    def create_indexes(coll_name: str) -> None:
        coll = db_connector.get_collection(coll_name)
        coll.create_index([("ios_id", 1), ("android_id", 1)], unique=True)
