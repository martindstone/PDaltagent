import os
from celery import Celery


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).lower() not in ('false', '0', 'no', 'off', '')

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://root:example@mongo:27017/')

PDAGENTD_ADMIN_USER = os.getenv('PDAGENTD_ADMIN_USER', 'pdaltagent@example.com')
PDAGENTD_ADMIN_PASS = os.getenv('PDAGENTD_ADMIN_PASS', 'pdaltagent')
PDAGENTD_ADMIN_DB = os.getenv('PDAGENTD_ADMIN_DB', 'pdaltagent-admin')
SUPERVISOR_USER = os.getenv('SUPERVISOR_USER', 'pdaltagent')
SUPERVISOR_PASS = os.getenv('SUPERVISOR_PASS', 'pdaltagent')
SUPERVISOR_URL = os.getenv('SUPERVISOR_URL', f"http://{SUPERVISOR_USER}:{SUPERVISOR_PASS}@localhost:9001/RPC2")

PD_API_TOKEN = os.environ.get("PDAGENTD_API_TOKEN")
WEBHOOK_DEST_URL = os.environ.get("PDAGENTD_WEBHOOK_DEST_URL")
IS_OVERVIEW = 'false' if env_flag("PDAGENTD_GET_ALL_LOG_ENTRIES") else 'true'
POLLING_INTERVAL_SECONDS = 10
if os.environ.get("PDAGENTD_POLLING_INTERVAL_SECONDS"):
    try:
        POLLING_INTERVAL_SECONDS = int(os.environ.get("PDAGENTD_POLLING_INTERVAL_SECONDS"))
    except Exception:
        pass

# keep activity db rows for 30 days
KEEP_ACTIVITY_SECONDS = 30 * 24 * 60 * 60
if os.environ.get("PDAGENTD_KEEP_ACTIVITY_SECONDS"):
    try:
        KEEP_ACTIVITY_SECONDS = int(os.environ.get("PDAGENTD_KEEP_ACTIVITY_SECONDS"))
    except Exception:
        pass

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'pyamqp://pdaltagent:pdaltagent@rabbit//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
try:
    CELERY_PREFETCH = int(os.getenv('PDAGENTD_PREFETCH_MULTIPLIER', '1'))
except ValueError:
    CELERY_PREFETCH = 1

try:
    CELERY_CONCURRENCY = int(os.getenv('PDAGENTD_WORKER_CONCURRENCY', '0'))
    if CELERY_CONCURRENCY <= 0:
        CELERY_CONCURRENCY = None
except ValueError:
    CELERY_CONCURRENCY = None

try:
    CELERY_MAX_TASKS_PER_CHILD = int(os.getenv('PDAGENTD_MAX_TASKS_PER_CHILD', '0'))
    if CELERY_MAX_TASKS_PER_CHILD <= 0:
        CELERY_MAX_TASKS_PER_CHILD = None
except ValueError:
    CELERY_MAX_TASKS_PER_CHILD = None

CELERY_WORKER_SEND_EVENTS = env_flag('PDAGENTD_WORKER_SEND_EVENTS', False)

app = Celery('tasks')
celery_config = {
    "broker_url": CELERY_BROKER_URL,
    "result_backend": CELERY_RESULT_BACKEND,
    "worker_prefetch_multiplier": CELERY_PREFETCH,
    "worker_send_task_events": CELERY_WORKER_SEND_EVENTS,
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "task_acks_late": True,
}
if CELERY_CONCURRENCY is not None:
    celery_config["worker_concurrency"] = CELERY_CONCURRENCY
if CELERY_MAX_TASKS_PER_CHILD is not None:
    celery_config["worker_max_tasks_per_child"] = CELERY_MAX_TASKS_PER_CHILD

app.conf.update(**celery_config)

app.conf.task_routes = {
    'pdaltagent.tasks.send_to_pd': {'queue': 'pd_events'},
    'pdaltagent.tasks.send_webhook': {'queue': 'pd_webhooks'},
    'pdaltagent.periodic_tasks.*': {'queue': 'pd_periodic'},
}
