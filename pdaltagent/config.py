import os
from celery import Celery

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://root:example@mongo:27017/')

PDAGENTD_ADMIN_USER = os.getenv('PDAGENTD_ADMIN_USER', 'pdaltagent@example.com')
PDAGENTD_ADMIN_PASS = os.getenv('PDAGENTD_ADMIN_PASS', 'pdaltagent')
PDAGENTD_ADMIN_DB = os.getenv('PDAGENTD_ADMIN_DB', 'pdaltagent-admin')
SUPERVISOR_USER = os.getenv('SUPERVISOR_USER', 'pdaltagent')
SUPERVISOR_PASS = os.getenv('SUPERVISOR_PASS', 'pdaltagent')
SUPERVISOR_URL = os.getenv('SUPERVISOR_URL', f"http://{SUPERVISOR_USER}:{SUPERVISOR_PASS}@localhost:9001/RPC2")

PD_API_TOKEN = os.environ.get("PDAGENTD_API_TOKEN")
WEBHOOK_DEST_URL = os.environ.get("PDAGENTD_WEBHOOK_DEST_URL")
IS_OVERVIEW = 'false' if os.environ.get("PDAGENTD_GET_ALL_LOG_ENTRIES") and os.environ.get("PDAGENTD_GET_ALL_LOG_ENTRIES").lower != 'false' else 'true'
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

app = Celery('tasks')

app.conf.task_routes = {
	'pdaltagent.tasks.send_to_pd': { 'queue': 'pd_events' },
	'pdaltagent.tasks.send_webhook': { 'queue': 'pd_webhooks' },
	'pdaltagent.periodic_tasks.*': { 'queue': 'pd_periodic' },
}
