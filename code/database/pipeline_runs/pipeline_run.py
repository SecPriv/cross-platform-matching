"""
Module managing pipeline run entities.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from time import time
from typing import Literal, Optional
from random import SystemRandom

from bson import ObjectId
from pymongo.collection import Collection, ReturnDocument

from database.db_connector import get_collection, PIPELINE_RUN_COLLECTION

_rng = SystemRandom()
_hostname = os.uname().nodename


def create_pipeline_run(tool_args: dict, tool_name: str) -> PipelineRun:
    """
    Inserts a new PipelineRun into the database
    """
    pipeline_run = PipelineRun(
        tool=tool_name,
        tool_args=tool_args
    ).insert()
    return pipeline_run


def update_pipeline_run(pipeline_run: PipelineRun, status: str) -> PipelineRun:
    """
    Updates the given PipelineRun with a status
    """
    pipeline_run.end_time = datetime.now()
    pipeline_run.state = status
    pipeline_run = pipeline_run.update()
    return pipeline_run


# noinspection PyDataclass
@dataclass(kw_only=True)
class PipelineRun:
    """
    A pipeline run groups the results based on when they were created.
    """

    @staticmethod
    def collection() -> Collection:
        """
        Get the collection of the pipeline runs
        """
        return get_collection(PIPELINE_RUN_COLLECTION)

    @staticmethod
    def find(*args, **kwargs) -> list[PipelineRun]:
        """
        Find pipeline runs.

        For possible arguments see:
        https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.find
        """
        return [
            PipelineRun(**result)
            for result in PipelineRun.collection().find(*args, **kwargs)
        ]

    @staticmethod
    def generate_run_id() -> str:
        """
        Generate a random run_id. Mostly guaranteed to be unique, as it uses the
        current timestamp in ms, plus the host name, plus a random number between 0
        and 1023.
        """
        return f"{int(time() * 1000)}-{_hostname}-{_rng.randrange(1024)}"

    _id: Optional[ObjectId] = None
    run_id: str = field(default_factory=lambda: PipelineRun.generate_run_id())

    tool: str
    tool_args: dict

    state: Literal["pending", "success", "failure"] = field(default="pending")

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def insert(self) -> PipelineRun:
        """
        Inserts a new pipeline run into the database.
        """
        entity = self.__dict__.copy()  # Copy to avoid side effects
        del entity["_id"]
        result = self.collection().insert_one(entity)
        return PipelineRun(
            **PipelineRun.collection().find_one({"_id": result.inserted_id})
        )

    def update(self) -> PipelineRun:
        """
        Persist the updates done to this pipeline run to the database. The _id of
        the object must be set, else a ValueError is raised.
        """
        if self._id is None:
            raise ValueError("_id must be set when updating PipelineRun")
        without_id = self.__dict__.copy()  # Copy to avoid side effects
        del without_id["_id"]
        with_id = {"_id": self._id}
        result = self.collection().find_one_and_update(
            filter=with_id,
            update={"$set": without_id, "$setOnInsert": with_id},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return PipelineRun(**result)


if __name__ == "__main__":
    print("Total pipeline runs currently in the DB")
    print(PipelineRun.collection().count_documents({}))

    print("Peek last 5 runs:")
    print(list(PipelineRun.find(sort=[("started_at", -1)], limit=5)))
