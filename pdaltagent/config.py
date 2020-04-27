from celery import Celery

app = Celery('tasks')

app.conf.task_routes = {
	'pdaltagent.tasks.send_to_pd': { 'queue': 'pd_events' },
	'pdaltagent.tasks.send_webhook': { 'queue': 'pd_webhooks' },
	'pdaltagent.tasks.poll_pd_log_entries': { 'queue': 'pd_poller' },
	'pdaltagent.tasks.clean_activity_store': { 'queue': 'pd_poller' }
}