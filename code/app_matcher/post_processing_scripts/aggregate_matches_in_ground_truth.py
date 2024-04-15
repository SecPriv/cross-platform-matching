"""
Script for extracting all matching pairs, whose ios_id AND android_id is in the
set of ios_ids/android_ids of the ground truth.
"""
from database.db_connector import get_collection

android_apps_coll = get_collection("analysis_results_android_full_13_11_2023")
gt_coll = get_collection("ground_truth")
matches_coll = get_collection("matches_full_2023_11_17_FINAL")
matches_in_gt = get_collection("matches_full_2023_11_17_FINAL_in_gt_and_analyzed")

analyzed_android_ids = set[str]()

for android_app in android_apps_coll.find():
    analyzed_android_ids.add(android_app.get('app_id'))

gt_pairs = gt_coll.find(filter={
    'android_id': { '$in': list(analyzed_android_ids)}
})

gt_ios_ids = set[str]()
gt_android_ids = set[str]()

for pair in gt_pairs:
    gt_ios_ids.add(pair.get("ios_id"))
    gt_android_ids.add(pair.get("android_id"))

print("Starting query...")

# Filter only ios_ids, because this is very fast
matches = matches_coll.find(filter={"ios_id": {"$in": list(gt_ios_ids)}})

to_insert = []

for m in matches:
    # Check for the android_id in python, because this is faster than adding
    # this to the query
    if m.get("android_id") in gt_android_ids:
        to_insert.append(m)
        if len(to_insert) == 10000:
            print(f"Inserting {len(to_insert)} matches in ground truth")
            matches_in_gt.insert_many(to_insert, ordered=False)
            to_insert = []

if len(to_insert) != 0:
    print(f"Inserting {len(to_insert)} matches in ground truth")
    matches_in_gt.insert_many(to_insert, ordered=False)

print("Done")
