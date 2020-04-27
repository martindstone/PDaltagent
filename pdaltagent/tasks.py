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
is_overview = 'false' if os.environ.get("GET_ALL_LOG_ENTRIES") and os.environ.get("GET_ALL_LOG_ENTRIES").lower != 'false' else 'true'
polling_interval_seconds = 10

# keep activity db rows for 30 days
keep_activity_seconds = 30*24*60*60

try:
    polling_interval_seconds = int(os.environ.get("POLLING_INTERVAL"))
except:
    pass

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    if not token:
        print(f"Can't get log entries because no token is set. Please set PD_API_TOKEN environment variable if you want to poll PD log entries")
        return

    if not webhook_dest_url:
        print(f"Can't send webhooks because no destination URL is set. Please set WEBHOOK_DEST_URL environment variable if you want to send webhooks")
        return

    sender.add_periodic_task(float(polling_interval_seconds), poll_pd_log_entries.s())
    sender.add_periodic_task(30.0, clean_activity_store.s())

@app.task(autoretry_for=(HTTPError,),
          retry_kwargs={'max_retries': 10},
          retry_backoff=15,
          retry_backoff_max=60*60*2)
def send_to_pd(routing_key, payload):
    return (routing_key, pd.send_v2_event(routing_key, payload))

@app.task(autoretry_for=(HTTPError,),
          retry_kwargs={'max_retries': 10},
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
    last_poll = a[1] if a else (now - datetime.timedelta(seconds=polling_interval_seconds))

    since = last_poll.replace(microsecond=0).isoformat()
    until = now.replace(microsecond=0).isoformat()

    params = {'since': since, 'until': until, 'is_overview': is_overview}
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

@app.task()
def clean_activity_store():
    conn = sqlite3.connect('/tmp/activity_store.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    d = datetime.datetime.utcnow() - datetime.timedelta(seconds=keep_activity_seconds)
    c.execute("delete from log_entries where created_at < ?", (d,))
    conn.commit()
    r = c.rowcount
    c.close()
    conn.close()
    return f"{r} rows deleted"

def consume():
    app.worker_main(['worker', '-A', 'pdaltagent.tasks', '-E', '-l', 'info'])
