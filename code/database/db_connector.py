"""
Module for managing the DB connection.
"""
import os
import pymongo as mongo
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URL: str = os.getenv(
    "MONGO_URL", "mongodb://localadmin:localadmin@localhost/"
)
MONGO_DB: str = os.getenv("MONGO_DB", "ios_android_dataset")

APPS_COLLECTION = "downloaded_apps"
ANALYSIS_RESULTS_COLLECTION = "analysis_results"
PIPELINE_RUN_COLLECTION = "pipeline_runs"

_client = mongo.MongoClient(MONGO_URL)

_db = _client[MONGO_DB]


def create_db_indexes():
    try:
        # Create a unique index on the "run_id" field of the "pipeline_runs" collection
        get_collection(PIPELINE_RUN_COLLECTION).create_index("run_id", unique=True)
        # Create unique indexes on "app_id", "result_type", "app_hash" and "user_rating" fields of the "metadata" collection
        app_data_collection = get_collection(APPS_COLLECTION)
        app_data_collection.create_index("app_id", sparse=True)
        app_data_collection.create_index("result_type", sparse=True)
        app_data_collection.create_index("app_hash", sparse=True)
        app_data_collection.create_index("user_rating", sparse=True)
        # Create unique indexes on ... fields of the "analysis_results" collection
        analysis_results_collection = get_collection(ANALYSIS_RESULTS_COLLECTION)
        analysis_results_collection.create_index("run_id")
        analysis_results_collection.create_index("analysis_type")
        analysis_results_collection.create_index("os")
        analysis_results_collection.create_index("tool")

    except ServerSelectionTimeoutError as e:
        raise RuntimeError(f"Could not create index! {e}")


def get_collection(name: str) -> Collection:
    """
    Get a collection by name from the current MongoDB.
    """
    return _db[name]

def start_session():
    """
    Starts a new MongoDB session on the current client.
    """
    return _client.start_session()

def run_mongodb_command(*args, **kwargs):
    """
    Run a command against the MongoDB instance. For more info, please see MongoDB's documentation.
    """
    return _db.command(*args, **kwargs)

if __name__ == "__main__":
    print("Successfully connected to database")
    import json
    print(json.dumps(_client.server_info(), indent=2))
