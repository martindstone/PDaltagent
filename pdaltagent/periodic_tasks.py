import os
import logging
import datetime
import inspect
from func_timeout import func_timeout, FunctionTimedOut
import pdaltagent.pd as pd
from pdaltagent.plugin_host import PluginHost
from pdaltagent.config import app
from pdaltagent.config import MONGODB_URL, PD_API_TOKEN, WEBHOOK_DEST_URL, IS_OVERVIEW, POLLING_INTERVAL_SECONDS
from celery import chain
from pymongo import MongoClient

from croniter import croniter
from pdaltagent.tasks import send_to_pd, send_webhook

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
if os.getenv('PDAGENTD_DEBUG'):
    logger.level = logging.DEBUG

plugin_host = PluginHost(True if os.environ.get("PDAGENTD_DEBUG") else False)

@app.task()
def run_fetch_events_method(method_index):
    method = plugin_host.methods['fetch_events'][method_index]['method']
    try:
        timeout = float(plugin_host.methods['fetch_events'][method_index].get('fetch_interval', POLLING_INTERVAL_SECONDS))
    except:
        if not croniter.is_valid(plugin_host.methods['fetch_events'][method_index].get('fetch_interval')):
            logger.error(f"fetch_events task from module {inspect.getmodule(method).__name__} has an invalid fetch_interval!")
            return
        now = datetime.datetime.now()
        c = croniter(plugin_host.methods['fetch_events'][method_index].get('fetch_interval'), now)
        t1 = c.next()
        t2 = c.next()
        timeout = t2 - t1

    logger.info(f"Running fetch_events task from module {inspect.getmodule(method).__name__} with timeout {timeout}")
    try:
        events = func_timeout(timeout, method)
    except FunctionTimedOut:
        logger.warning(f"fetch_events task from module {inspect.getmodule(method).__name__} timed out after {timeout} seconds!")
        return

    if not isinstance(events, list):
        logger.warning(f"fetch_events method in plugin {inspect.getmodule(method.__self__).__name__} returned invalid value {events}")
        return

    logger.info(f"fetch_events method in plugin {inspect.getmodule(method.__self__).__name__} got events {events}")
    for event in events:
        if not (isinstance(event, dict) and
                'routing_key' in event and
                pd.is_valid_integration_key(event['routing_key']) and
                pd.is_valid_v2_payload(event)):
            logger.warning(f"fetch_events method in plugin {inspect.getmodule(method.__self__).__name__} returned a list containing an invalid event {event}")
            continue
        send_to_pd.delay(event['routing_key'], event, destination_type="v2")

@app.task()
def poll_pd_log_entries():
    client = MongoClient(MONGODB_URL)
    log_entries_coll = client.pdaltagent.log_entries

    now = datetime.datetime.utcnow()
    try:
        last_poll = log_entries_coll.find().sort("created_at", -1).limit(1)[0]['created_at']
        logger.info(f"got last poll {last_poll.isoformat()} from Mongo")
    except:
        last_poll = (now - datetime.timedelta(seconds=POLLING_INTERVAL_SECONDS))
        logger.info(f"made last poll {last_poll.isoformat()} from defaults")

    since = last_poll.replace(microsecond=0).isoformat()
    until = now.replace(microsecond=0).isoformat()

    params = {'since': since, 'until': until, 'is_overview': IS_OVERVIEW}
    iles = pd.fetch_log_entries(token=PD_API_TOKEN, params=params)
    iles.reverse()
    new_iles = []
    dups = 0
    ile_chains = {}
    for ile in iles:
        try:
            x = log_entries_coll.find({'id': ile['id']}).sort('created_at', -1).limit(1)[0]
            if x:
                logger.info(f"found dup ILE {ile['id']} from {x['created_at'].isoformat()}")
                dups += 1
                continue
        except:
            new_iles.append(ile)
            pass

        incident_id = ile['incident']['id']
        if not ile_chains.get(incident_id):
            ile_chains[incident_id] = []

        webhook_message = pd.ile_to_webhook(ile)
        if webhook_message == None:
            continue

        sig = send_webhook.si(WEBHOOK_DEST_URL, webhook_message)
        ile_chains[incident_id].append(sig)

    for incident_id, ile_chain in ile_chains.items():
        chain(ile_chain).delay()

    if len(new_iles):
        for ile in new_iles:
            ile['created_at'] = datetime.datetime.fromisoformat(ile['created_at'].rstrip('Z'))
        log_entries_coll.insert_many(new_iles)

    return f"{len(iles)} fetched, {len(new_iles)} processed, {dups} duplicates (since {since})"
