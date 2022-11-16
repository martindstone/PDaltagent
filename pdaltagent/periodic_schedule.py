import os
import logging
import inspect
from pdaltagent.config import app
from pdaltagent.plugin_host import PluginHost
from pdaltagent.config import MONGODB_URL, PD_API_TOKEN, WEBHOOK_DEST_URL, IS_OVERVIEW, POLLING_INTERVAL_SECONDS, KEEP_ACTIVITY_SECONDS
from pdaltagent.periodic_tasks import poll_pd_log_entries
from pymongo import MongoClient

from celery.utils.log import get_task_logger

from pdaltagent.periodic_tasks import run_fetch_events_method

plugin_host = PluginHost(True if os.environ.get("PDAGENTD_DEBUG") else False)

logger = get_task_logger(__name__)
if os.getenv('PDAGENTD_DEBUG'):
    logger.level = logging.DEBUG

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.debug(f"initializing periodic scheduler")

    for i, method in enumerate(plugin_host.methods['fetch_events']):
        fetch_interval = float(method.get('fetch_interval', POLLING_INTERVAL_SECONDS))
        logger.info(f"Adding fetch_events task from module {inspect.getmodule(method['method']).__name__} at interval {fetch_interval}")
        sender.add_periodic_task(fetch_interval, run_fetch_events_method.s(i))

    if not PD_API_TOKEN:
        logger.warning(f"Can't get log entries because no token is set. Please set PDAGENTD_API_TOKEN environment variable if you want to poll PD log entries")
    elif not WEBHOOK_DEST_URL:
        logger.warning(f"Can't send webhooks because no destination URL is set. Please set PDAGENTD_WEBHOOK_DEST_URL environment variable if you want to send webhooks")
    else:
        client = MongoClient(MONGODB_URL)
        log_entries_coll = client.pdaltagent.log_entries
        log_entries_coll.create_index("created_at", expireAfterSeconds=KEEP_ACTIVITY_SECONDS)
        sender.add_periodic_task(float(POLLING_INTERVAL_SECONDS), poll_pd_log_entries.s())

