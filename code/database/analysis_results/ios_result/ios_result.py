from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Self
from pymongo.collection import Collection
from bson.objectid import ObjectId

from database.db_connector import get_collection, ANALYSIS_RESULTS_COLLECTION


@dataclass(kw_only=True)
class iOSResult:
    """
    An iOS result is the base class for all static and dynamic iOS results. It holds all shared data
    between the different kind of results.
    """

    @staticmethod
    def collection() -> Collection:
        """
        Get the collection for the results. All result-types should use the same
        collection.
        """
        return get_collection(ANALYSIS_RESULTS_COLLECTION)

    run_id: str
    path: str
    app_id: str
    app_hash: str
    tool: str
    analysis_type: Literal["static", "dynamic"]
    # result_type: Literal["analysis-result", "app-store-info", "privacy-labels", "log"]
    raw_data: dict

    _id: Optional[ObjectId] = None
    os: Literal["iOS"] = field(default="iOS")
    created_at: datetime = field(default_factory=datetime.now)

    def insert(self: Self) -> Self:
        """
        Store this pipeline result in the database.
        """
        entity = self.__dict__.copy()
        del entity["_id"]
        result = self.collection().insert_one(entity)
        return self.__class__(
            **self.collection().find_one(filter={"_id": result.inserted_id})
        )


if __name__ == "__main__":
    print("Total iOS results currently in the DB:")
    print(iOSResult.collection().count_documents({}))

    print("Total iOS results per tool:")
    print(
        list(
            iOSResult.collection().aggregate(
                [{"$group": {"_id": "$tool", "count": {"$count": {}}}}]
            )
        )
    )
