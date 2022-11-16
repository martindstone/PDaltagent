import os
import time
import pdaltagent.pd as pd
import requests
import logging
import json
import random
from requests import HTTPError
from pdaltagent.config import app
from pdaltagent.plugin_host import PluginHost
from celery.utils.log import get_task_logger
from celery import Task

class SendTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Failed to send {args[1]!r} to {args[0]}: {exc}")

plugin_host = PluginHost(True if os.environ.get("PDAGENTD_DEBUG") else False)

logger = get_task_logger(__name__)
if os.getenv('PDAGENTD_DEBUG'):
    logger.level = logging.DEBUG

@app.task(base=SendTask,
          bind=True,
          throws=(HTTPError,),
          retry_backoff=True,
          max_retries=None,
          acks_late=True)
def send_to_pd(self, routing_key, payload, base_url="https://events.pagerduty.com", destination_type="v2"):
    logger.debug(f"Before filter event, routing key: {routing_key}, type: {destination_type}, payload: {json.dumps(payload)}")
    time_before_filter = time.time()
    r = plugin_host.filter_event(payload, routing_key, destination_type)
    time_after_filter = time.time()
    filter_time = round(time_after_filter - time_before_filter, 2)
    if ( filter_time > 5):
        logger.warning(f"Event filtering took too long! ({filter_time} seconds) for event: {json.dumps(payload)}")
    if r is None:
        return ('event suppressed', json.dumps(payload))
    (_payload, _routing_key, _destination_type) = r
    logger.debug(f"After filter event, routing key: {_routing_key}, type: {_destination_type}, payload: {json.dumps(_payload)}")
    r = None
    try:
        r = pd.send_event(_routing_key, _payload, base_url, _destination_type)
    except HTTPError as e:
        if e.response.status_code == 429:
            raise self.retry(exc=e, countdown=int(random.uniform(3, 5) * (self.request.retries + 1)))
        raise e
    return (_routing_key, r)

@app.task(base=SendTask,
          bind=True,
          throws=(HTTPError,),
          retry_backoff=15)
def send_webhook(self, url, payload):
    logger.debug(f"Before filter webhook, url: {url}, payload: {json.dumps(payload)}")
    time_before_filter = time.time()
    r = plugin_host.filter_webhook(payload, url)
    time_after_filter = time.time()
    filter_time = round(time_after_filter - time_before_filter, 2)
    if ( filter_time > 5):
        logger.warning(f"Webhook filtering took too long! ({filter_time} seconds) for webhook: {json.dumps(payload)}")
    if r is None:
        return ('webhook suppressed', url, json.dumps(payload))
    (_payload, _url) = r
    logger.debug(f"After filter webhook, url: {_url}, payload: {json.dumps(_payload)}")
    r = None
    try:
        r = requests.post(_url, json=_payload)
    except HTTPError as e:
        if e.response.status_code == 429:
            raise self.retry(exc=e, countdown=int(random.uniform(3, 5) * (self.request.retries + 1)))
        raise e
    return (_url, r)
