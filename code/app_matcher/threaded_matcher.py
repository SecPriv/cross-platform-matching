import os
import traceback
from argparse import ArgumentParser
from concurrent import futures
from math import ceil
from typing import Callable, TypeVar

from pymongo.collection import Collection
from app_matcher.matchers import (
    ALL_CLEANUPS,
    ALL_INDEXED_MATCHERS,
    ALL_MATCHERS,
    ALL_PREPARES,
    ALL_WEIGHT_MODIFIERS,
)
from database.analysis_results.preprocessing_result.android_preprocessing_result.android_preprocessing_result import (
    AndroidPreprocessingResult,
)
from database.analysis_results.preprocessing_result.ios_preprocessing_result.ios_preprocessing_result import (
    iOSPreprocessingResult,
)
from database.db_connector import get_collection
from database.matching_results.matching_result import MatchingResult

_Result = TypeVar("_Result")


def _safe_call(fn: Callable[..., _Result], args: dict[str, any]) -> _Result:
    relevant_args = {
        key: args[key] for key in args.keys() if key in fn.__code__.co_varnames
    }
    return fn(**relevant_args)


def _match_ios_to_android(
    target_index: int,
    target: iOSPreprocessingResult,
    candidate_index: int,
    candidate: AndroidPreprocessingResult,
    matchers=ALL_MATCHERS,
    index_matchers=ALL_INDEXED_MATCHERS,
) -> MatchingResult:
    scores = {}
    # weight_modifiers = {}
    for matcher in matchers:
        scores = scores | _safe_call(
            matcher, {"ios_app": target, "android_app": candidate}
        )

    for matcher in index_matchers:
        scores = scores | _safe_call(
            matcher,
            {
                "ios_app": target,
                "android_app": candidate,
                "ios_index": target_index,
                "android_index": candidate_index,
            },
        )

    # for modifier in ALL_WEIGHT_MODIFIERS:
    #     weight_modifiers = weight_modifiers | modifier(target, candidate)

    # weights = {
    #     "privacy_url_weight": 2,
    #     "developer_url_weight": 2,
    #     "developer_weight": 2,
    #     "app_id_weight": 1,
    #     "app_name_weight": 3,
    #     "deep_link_weight": 1,
    #     "icon_hash_weight": 3,
    #     "description_weight": 0 if (not weight_modifiers.get('description_language_matches') and (scores.get("description_cosine_similarity") < 0.8)) else (1 if scores.get("description_cosine_similarity") < 0.8 else 3)
    # }

    total_score = sum(scores.values())
    average_score = total_score / len(scores)

    # def _linear(x: float, k: float = 2.5, d: float = -0.75):
    #     y = k * x + d
    #     if y < 0:
    #         return 0
    #     elif y > 1:
    #         return 1
    #     else:
    #         return y

    # linear_score = (
    #     _linear(scores.get("privacy_url_max"))
    #     # +
    #     # _linear(scores.get("developer_url_max"))
    #     + _linear(scores.get("developer_max"))
    #     + _linear(scores.get("app_id_max"))
    #     + _linear(scores.get("app_name_max"))
    #     + _linear(scores.get("deep_link_max"))
    #     + _linear(scores.get("icon_hash_max"))
    #     + _linear(scores.get("description_cosine_similarity"))
    # ) / (len(ALL_MATCHERS))

    # weighted_score = (
    #     scores.get("privacy_url_max") * weights.get("privacy_url_weight")
    #     +
    #     _linear(scores.get("privacy_url_max")) * weights.get("developer_url_weight")
    #     +
    #     scores.get("developer_max") * weights.get("developer_weight")
    #     +
    #     scores.get("app_id_max") * weights.get("app_id_weight")
    #     +
    #     scores.get("app_name_max") * weights.get("app_name_weight")
    #     +
    #     scores.get("deep_link_max") * weights.get("deep_link_weight")
    #     +
    #     scores.get("icon_hash_max") * weights.get("icon_hash_weight")
    #     +
    #     scores.get("description_cosine_similarity") * weights.get("description_weight")
    # ) / (sum(weights.values()))

    return MatchingResult(
        ios_id=target.app_id,
        android_id=candidate.app_id,
        scores=scores,
        weighted_score=None,
        average_score=average_score,
        linear_score=None,
    )


def _match_executor(
    target_start_index: int,
    targets: list[iOSPreprocessingResult],
    candidates: list[AndroidPreprocessingResult],
    matcher_coll_name: str,
    matchers=ALL_MATCHERS,
    index_matchers=ALL_INDEXED_MATCHERS,
):
    print(
        f"Starting process for {len(targets)} iOS apps and {len(candidates)} Android apps"
    )
    """
    Task run inside a thread. It will calculate the matching scores for all candidates
    for the given target and persist their results.
    """
    to_be_inserted = []
    matcher_coll = get_collection(matcher_coll_name)
    for target_index, target in enumerate(targets, start=target_start_index):
        for candidate_index, candidate in enumerate(candidates):
            try:
                matches = _match_ios_to_android(
                    target_index=target_index,
                    target=target,
                    candidate_index=candidate_index,
                    candidate=candidate,
                    matchers=matchers,
                    index_matchers=index_matchers,
                )
                entity = matches.__dict__
                del entity["_id"]
                to_be_inserted.append(entity)

                if len(to_be_inserted) >= 10000:
                    # bulk insert for better performance, also we set ordered to false so the documents can be inserted in arbitrary order
                    # see https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.insert_many
                    matcher_coll.insert_many(to_be_inserted, ordered=False)
                    # print(f'[Worker] Inserted {len(to_be_inserted)} matches')
                    to_be_inserted = []

            except Exception as err:
                # TODO: pack error so that it can be properly logged/stored
                print(err)
                print(traceback.format_exc())
                pass

    # insert remaining candidates
    if len(to_be_inserted) > 0:
        try:
            matcher_coll.insert_many(to_be_inserted, ordered=False)
            to_be_inserted = []
        except Exception as err:
            # TODO: pack error so that it can be properly logged/stored
            print(err)
            print(traceback.format_exc())
            pass

    print(f"Process finished")


def match_all(
    ios_apps: list[iOSPreprocessingResult],
    android_apps: list[AndroidPreprocessingResult],
    matches_coll_name: str,
    threads: int = os.cpu_count() - 2,  # Max number of matcher threads
    matchers=ALL_MATCHERS,
    index_matchers=ALL_INDEXED_MATCHERS,
):
    """
    Iterate over given apps and spawn a task for each of them to match all possible candidates.
    The number of threads is limited by the "threads" parameter.
    """

    chunk_size = ceil(len(ios_apps) / threads)
    work_chunks = list(
        map(
            lambda x: ios_apps[x * chunk_size : x * chunk_size + chunk_size],
            list(range(threads)),
        )
    )
    runningTasks = set[futures.Future[None]]()
    with futures.ProcessPoolExecutor(max_workers=threads) as pool:
        for chunk_index, chunk in enumerate(work_chunks):
            runningTasks.add(
                pool.submit(
                    _match_executor,
                    chunk_index * chunk_size,
                    chunk,
                    android_apps,
                    matches_coll_name,
                    matchers=matchers,
                    index_matchers=index_matchers,
                )
            )

    # Flush remaining results
    for future in runningTasks:
        try:
            future.result()
        except Exception as e:
            # TODO: Properly handle error
            print(traceback.format_exc())
            print(e)


_T = TypeVar("_T")


def _fetch_all(coll: Collection[_T], constructor: Callable[[], _T]) -> list[_T]:
    cursor = coll.find()
    targets: list[_T] = []
    for doc in cursor:
        targets.append(constructor(**doc))
    return targets


def match_all_documents(
    ios_coll_name: str,
    android_coll_name: str,
    matches_coll_name: str,
    threads: int = os.cpu_count() - 2,
    preparations=ALL_PREPARES,
    matchers=ALL_MATCHERS,
    index_matchers=ALL_INDEXED_MATCHERS,
    cleanups=ALL_CLEANUPS,
):
    ios_coll: Collection[iOSPreprocessingResult] = get_collection(ios_coll_name)
    print("Loading all iOS apps...")
    ios_apps = _fetch_all(ios_coll, iOSPreprocessingResult)
    print(f"Loaded {len(ios_apps)} iOS apps")
    android_coll: Collection[AndroidPreprocessingResult] = get_collection(
        android_coll_name
    )
    print("Loading all Android apps...")
    android_apps = _fetch_all(android_coll, AndroidPreprocessingResult)
    print(f"Loaded {len(android_apps)} Android apps")
    print("Loaded all apps into memory")

    print("Preparing matchers...")
    for prepare in preparations:
        prepare(ios_apps=ios_apps, android_apps=android_apps)

    print("Running all matchers")
    match_all(
        ios_apps=ios_apps,
        android_apps=android_apps,
        matches_coll_name=matches_coll_name,
        threads=threads,
        matchers=matchers,
        index_matchers=index_matchers,
    )

    print("Cleaning up resources")
    for cleanup in cleanups:
        cleanup()


if __name__ == "__main__":
    args_parser = ArgumentParser(
        description="""Find matching Android apps and iOS apps from two datasets."""
    )

    default_threads = os.cpu_count() - 2

    args_parser.add_argument(
        "--ios-collection",
        help="Collection to extract the iOS data from. The documents in the collection must conform to the iOSPreprocessingResult entity.",
        required=True,
    )
    args_parser.add_argument(
        "--android-collection",
        help="Collection to extract the Android data from. The documents in the collection must conform to the AndroidPreprocessingResult entity.",
        required=True,
    )
    args_parser.add_argument(
        "--matches-collection",
        help="Collection to store the resulting matches to. The matches collection can already contain entities. All documents in the collection must conform to the MatchingResult entity.",
        required=True,
    )
    args_parser.add_argument(
        "--threads",
        help=f"Set number of threads to use. Defaults to number of cores - 2 (={default_threads} on your machine)",
        type=int,
        default=default_threads,
    )
    args = args_parser.parse_args()

    print("Creating matcher indexes")
    MatchingResult.create_indexes(args.matches_collection)

    print("Start matching all apps")
    match_all_documents(
        ios_coll_name=args.ios_collection,
        android_coll_name=args.android_collection,
        matches_coll_name=args.matches_collection,
        threads=args.threads,
    )
    print("All done")
