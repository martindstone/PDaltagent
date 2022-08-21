import os
import json
import datetime
import pdaltagent.pd as pd
import requests
import sqlite3
import random
from requests import HTTPError
from pdaltagent.config import app
from celery.utils.log import get_task_logger
from celery import chain, Task

logger = get_task_logger(__name__)

PD_API_TOKEN = os.environ.get("PDAGENTD_API_TOKEN")
WEBHOOK_DEST_URL = os.environ.get("PDAGENTD_WEBHOOK_DEST_URL")
IS_OVERVIEW = 'false' if os.environ.get("PDAGENTD_GET_ALL_LOG_ENTRIES") and os.environ.get("PDAGENTD_GET_ALL_LOG_ENTRIES").lower != 'false' else 'true'
LOG_EVENTS = os.environ.get("PDAGENTD_LOG_EVENTS", False)

POLLING_INTERVAL_SECONDS = 10
if os.environ.get("PDAGENTD_POLLING_INTERVAL_SECONDS"):
    try:
        POLLING_INTERVAL_SECONDS = int(os.environ.get("PDAGENTD_POLLING_INTERVAL_SECONDS"))
    except:
        pass

# keep activity db rows for 30 days
KEEP_ACTIVITY_SECONDS = 30*24*60*60
if os.environ.get("PDAGENTD_KEEP_ACTIVITY_SECONDS"):
    try:
        KEEP_ACTIVITY_SECONDS = int(os.environ.get("PDAGENTD_KEEP_ACTIVITY_SECONDS"))
    except:
        pass

class SendTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.warn(f"Failed to send {args[1]!r} to {args[0]}: {exc}")

@app.on_after_finalize.connect
def check_activity_store(sender, **kwargs):
    conn = sqlite3.connect('/tmp/activity_store.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='log_entries'")
    if c.fetchone()[0]==0:
        print('Activity store table does not exist. Creating...')
        c.executescript("""
            BEGIN TRANSACTION;
            CREATE TABLE log_entries (
                            id TEXT NOT NULL,
                            created_at timestamp);
            COMMIT;
        """)

    conn.commit()
    conn.close()

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if not PD_API_TOKEN:
        print(f"Can't get log entries because no token is set. Please set PDAGENTD_API_TOKEN environment variable if you want to poll PD log entries")
        return

    if not WEBHOOK_DEST_URL:
        print(f"Can't send webhooks because no destination URL is set. Please set PDAGENTD_WEBHOOK_DEST_URL environment variable if you want to send webhooks")
        return

    sender.add_periodic_task(float(POLLING_INTERVAL_SECONDS), poll_pd_log_entries.s())
    sender.add_periodic_task(float(KEEP_ACTIVITY_SECONDS), clean_activity_store.s())

@app.task(base=SendTask,
          bind=True,
          throws=(HTTPError,),
          retry_backoff=True,
          max_retries=None,
          acks_late=True)
def send_to_pd(self, routing_key, payload, base_url="https://events.pagerduty.com", destination_type="v2"):
    if LOG_EVENTS:
        logger.info(f"Sending {payload!r} to routing key {routing_key}, base URL {base_url}, type {destination_type}")
    r = None
    try:
        r = pd.send_event(routing_key, payload, base_url, destination_type)
    except HTTPError as e:
        if e.response.status_code == 429:
            raise self.retry(exc=e, countdown=int(random.uniform(10, 15) * (self.request.retries + 1)))
        raise e
    return (routing_key, r)

@app.task(base=SendTask,
          throws=(HTTPError,),
          retry_backoff=15)
def send_webhook(url, payload):
    return (url, requests.post(url, json=payload))

@app.task()
def poll_pd_log_entries():
    conn = sqlite3.connect('/tmp/activity_store.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    r = c.execute('select * from log_entries order by created_at desc limit 1')
    a = r.fetchone()
    now = datetime.datetime.utcnow()
    last_poll = a[1] if a else (now - datetime.timedelta(seconds=POLLING_INTERVAL_SECONDS))

    since = last_poll.replace(microsecond=0).isoformat()
    until = now.replace(microsecond=0).isoformat()

    params = {'since': since, 'until': until, 'is_overview': IS_OVERVIEW}
    iles = pd.fetch_log_entries(token=PD_API_TOKEN, params=params)
    iles.reverse()
    new_iles = []
    dups = 0
    ile_chains = {}
    for ile in iles:
        ile_id = ile['id']
        r = c.execute("select count(*) from log_entries where id = ?", (ile_id,))
        if r.fetchone()[0]:
            dups += 1
            continue

        created_at = datetime.datetime.fromisoformat(ile['created_at'].rstrip('Z'))
        new_iles.append((ile_id, created_at))

        incident_id = ile['incident']['id']
        if not ile_chains.get(incident_id):
            ile_chains[incident_id] = []

        webhook_message = pd.ile_to_webhook(ile)
        if webhook_message == None:
            continue

        sig = send_webhook.si(WEBHOOK_DEST_URL, webhook_message)
        ile_chains[incident_id].append(sig)

    c.executemany('insert into log_entries values (?, ?)', new_iles)
    conn.commit()
    c.close()
    conn.close()
    for incident_id, ile_chain in ile_chains.items():
        chain(ile_chain).delay()
    return f"{len(iles)} fetched, {len(new_iles)} processed, {dups} duplicates (since {since})"

@app.task()
def clean_activity_store():
    conn = sqlite3.connect('/tmp/activity_store.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    d = datetime.datetime.utcnow() - datetime.timedelta(seconds=KEEP_ACTIVITY_SECONDS)
    c.execute("delete from log_entries where created_at < ?", (d,))
    conn.commit()
    r = c.rowcount
    c.close()
    conn.close()
    return f"{r} rows deleted"

def consume():
    app.worker_main(['-A', 'pdaltagent.tasks', 'worker', '-n', 'events', '-Q', 'pd_events', '-E', '-l', 'info'])

def poll():
    app.worker_main(['-A', 'pdaltagent.tasks', 'worker', '-n', 'poller', '-B', '-Q', 'pd_poller,pd_webhooks', '-E', '-l', 'info'])
