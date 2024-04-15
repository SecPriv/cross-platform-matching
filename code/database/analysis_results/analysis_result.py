

from abc import ABC
from dataclasses import dataclass
import datetime
from typing import Collection, Literal, Optional, Self
from bson import ObjectId

from pymongo import ReturnDocument

import database.db_connector as db_connector


@dataclass(kw_only=True)
class AnalysisResult(ABC):

    @staticmethod
    def _get_discriminator() -> dict:
        return None

    @staticmethod
    def collection() -> Collection:
        """
        Get the collection for the apps, as metadata is stored with the apps.
        """
        return db_connector.get_collection(db_connector.ANALYSIS_RESULTS_COLLECTION)

    _id: Optional[ObjectId] = None
    run_id: str
    path: str
    app_id: str
    app_hash: str
    tool: str
    created_at: datetime.datetime
    analysis_type: Literal["static", "dynamic"]
    os: Literal["iOS", "Android"]

    def upsert(self: Self) -> Self:
        """
        Store iOS app data in the database.
        """
        entity = self.__dict__.copy() # Copy to avoid side-effects
        if '_id' in entity:
            del entity["_id"]
        result = self.collection().find_one_and_update(filter={"run_id": self.run_id, "app_hash": self.app_hash, "analysis_type": self.analysis_type, "os": self.os}, 
                                                       update={"$set": entity}, 
                                                       upsert=True,
                                                       return_document=ReturnDocument.AFTER)
        # Use self.__class__ for using runtime type instead of
        return self.__class__(
            **result
        )    