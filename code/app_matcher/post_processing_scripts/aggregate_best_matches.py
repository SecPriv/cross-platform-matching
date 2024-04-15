from concurrent import futures
import logging
from pymongo import monitoring
from database.db_connector import get_collection

# Requires the PyMongo package.
# https://api.mongodb.com/python/current


log = logging.getLogger()
log.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


class CommandLogger(monitoring.CommandListener):

    def started(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} started on server "
                 "{0.connection_id}".format(event))

    def succeeded(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} on server {0.connection_id} "
                 "succeeded in {0.duration_micros} "
                 "microseconds".format(event))

    def failed(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} on server {0.connection_id} "
                 "failed in {0.duration_micros} "
                 "microseconds".format(event))

# monitoring.register(CommandLogger())

matches = get_collection('matches_full_2023_12_21_name_exact_match')
unique_ios_ids = matches.aggregate([
    {
        '$group': {
            '_id': '$ios_id'
        }
    }
])

best_matches = get_collection('best_matches_2023_12_21_name_exact_match')

log.info('Finished Aggregation! Starting insert...')

def persist_best_match_for(ios_id: str) -> None:
    log.debug(f'Getting best match for: {ios_id}')
    best_match = matches.find_one({ 'ios_id': ios_id}, sort=[('average_score', -1)], limit=1)
    if best_match is None:
        log.error(f'No best match found for {ios_id}!')
        return
    log.debug(f'Best match for "{ios_id}": {best_match.get("android_id")}')
    best_matches.find_one_and_update({'_id': ios_id}, { "$set": {"best_match": best_match}}, upsert=True)

with futures.ThreadPoolExecutor(max_workers=10) as pool:
    running_tasks = set[futures.Future[None]]()
    for ios_id_group in unique_ios_ids:
        if len(running_tasks) >= 1000:
                runningTasksCopy = running_tasks.copy()
                for future in runningTasksCopy:
                    if future.running():
                        continue
                    running_tasks.remove(future)
                    future.result()

                # Check if we removed any futures from running MatchingResults
                if len(running_tasks) >= 1000:
                    # Partition the futures into completed and incomplete futures.
                    # Return as soon as there is is one completed future
                    completed, running_tasks = futures.wait(
                        running_tasks, return_when=futures.FIRST_COMPLETED
                    )
        log.debug(f'Submitting matcher for {ios_id_group.get("_id")}')
        running_tasks.add(pool.submit(persist_best_match_for, ios_id_group.get('_id')))
    futures.wait(running_tasks)

log.info('All done')

# for result in results:
#     i += 1
#     log.info(i)
#     collection.insert_one(result)
    
