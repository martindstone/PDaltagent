import os
import json
import datetime
import pdaltagent.pd as pd
import requests
import sqlite3
from requests import HTTPError
from pdaltagent.config import app
from celery.utils.log import get_task_logger

token = os.environ.get("PD_API_TOKEN")
webhook_dest_url = os.environ.get("WEBHOOK_DEST_URL")
polling_interval_seconds = 10
try:
    polling_interval_seconds = int(os.environ.get("POLLING_INTERVAL"))
except:
    pass

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, poll_pd_log_entries.s())

@app.task(autoretry_for=(HTTPError,),
          retry_kwargs={'max_retries': 10},
          retry_backoff=15,
          retry_backoff_max=60*60*2)
def send_to_pd(routing_key, payload):
    logger = get_task_logger(__name__)
    logger.info(f"sending to {routing_key}")
    return pd.send_v2_event(routing_key, payload)

@app.task(autoretry_for=(HTTPError,),
          retry_kwargs={'max_retries': 10},
          retry_backoff=15)
def send_webhook(url, payload):
    logger = get_task_logger(__name__)
    logger.info(f"sending webhook to {webhook_dest_url}")
    return requests.post(url, json=payload)


@app.task()
def poll_pd_log_entries():
    logger = get_task_logger(__name__)
    if not token:
        logger.info(f"Can't get log entries because no token is set. Please set PD_API_TOKEN environment variable")
        return

    if not webhook_dest_url:
        logger.info(f"Can't send webhooks because no destination URL is set. Please set WEBHOOK_DEST_URL environment variable")
        return

    conn = sqlite3.connect('/tmp/activity_store.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    r = c.execute('select * from log_entries order by created_at desc limit 1')
    a = r.fetchone()
    now = datetime.datetime.utcnow()
    last_poll = a[1] if a else (now - datetime.timedelta(seconds=polling_interval_seconds))

    since = last_poll.replace(microsecond=0).isoformat()
    until = now.replace(microsecond=0).isoformat()

    params = {'since': since, 'until': until}
    iles = pd.fetch_log_entries(token=token, params=params)
    new_iles = []
    dups = 0
    for ile in iles:
        ile_id = ile['id']
        r = c.execute("select count(*) from log_entries where id = ?", (ile_id,))
        if r.fetchone()[0]:
            dups += 1
            continue
        created_at = datetime.datetime.fromisoformat(ile['created_at'].rstrip('Z'))
        new_iles.append((ile_id, created_at))
        send_webhook.delay(webhook_dest_url, pd.ile_to_webhook(ile))
    c.executemany('insert into log_entries values (?, ?)', new_iles)
    conn.commit()
    c.close()
    conn.close()
    return f"{len(iles)} fetched, {len(new_iles)} processed, {dups} duplicates (since {since})"

def consume():
    app.worker_main(['worker', '-A', 'pdaltagent.tasks', '-E', '-l', 'info'])