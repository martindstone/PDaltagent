import pdaltagent.pd as pd
from requests import HTTPError
from pdaltagent.config import app
from celery.utils.log import get_task_logger

@app.task(autoretry_for=(HTTPError,),
          retry_kwargs={'max_retries': 10},
          retry_backoff=15,
          retry_backoff_max=60*60*2)
def send_to_pd(routing_key, payload):
    logger = get_task_logger(__name__)
    logger.info(f"sending to {routing_key}")
    return pd.send_v2_event(routing_key, payload)

def consume():
    app.worker_main(['worker', '-A', 'pdaltagent.tasks', '-E', '-l', 'info'])