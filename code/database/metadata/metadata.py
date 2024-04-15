"""
Abstract Module for common fields and methods of Apps and Store Data.
"""

from dataclasses import dataclass
from typing import Literal, Optional, Self
from bson.objectid import ObjectId
from pymongo.collection import ReturnDocument, Collection

from abc import ABC

from database.db_connector import get_collection, APPS_COLLECTION


@dataclass(kw_only=True)
class Metadata(ABC):
    """
    Abstract DTO superclass for apps and their store data, i.e. objects of the "app_metadata" collection.
    """

    @staticmethod
    def _get_discriminator() -> dict:
        return None

    @staticmethod
    def collection() -> Collection:
        """
        Get the collection for the apps, as metadata is stored with the apps.
        """
        return get_collection(APPS_COLLECTION)
    
    @classmethod
    def find(cls, filter: dict) -> list[Self]:
        """
        Find objects in the "ios_app_data" collection based on filter.
        """
        discriminator = cls._get_discriminator()
        if discriminator is not None:
            filter = filter | discriminator

        return [
            cls(**result) for result in cls.collection().find(filter=filter)
        ]

    _id: Optional[ObjectId] = None
    os: Literal["iOS", "Android"]            # discriminator
    result_type: Literal["app", "metadata"]  # discriminator
    run_id: str
    app_id: str
    app_hash: str
            
    def upsert(self: Self) -> Self:
        """
        Store iOS app data in the database.
        """
        entity = self.__dict__.copy() # Copy to avoid side-effects
        del entity["_id"]
        result = self.collection().find_one_and_update(filter={"app_hash": self.app_hash, "result_type": self.result_type, "os": self.os}, 
                                                       update={"$set": entity}, 
                                                       upsert=True,
                                                       return_document=ReturnDocument.AFTER)
        # Use self.__class__ for using runtime type instead of
        return self.__class__(
            **result
        )    
    
    def update(self: Self) -> Self:
        """
        Persist the updates done to this iOS app data to the database. The _id of
        the object must be set, else a ValueError is raised.
        """
        if self._id is None:
            raise ValueError("_id must be set when updating iOSApp")
        without_id = self.__dict__.copy()  # Copy to avoid side-effects
        del without_id["_id"]
        with_id = {"_id": self._id}
        result = self.collection().find_one_and_update(
            filter=with_id,
            update={"$set": without_id, "$setOnInsert": with_id},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self.__class__(**result)
    

if __name__ == "__main__":
    print("Total iOS apps currently in the DB:")
    print(Metadata.collection().count_documents({}))
