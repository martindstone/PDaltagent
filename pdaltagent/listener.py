#!/usr/bin/env python3

from pdaltagent.tasks import send_to_pd
from pdaltagent.scrubber import scrub
import pdaltagent.pd as pd
import os
import json

from flask import Flask, request
app = Flask(__name__)

SCRUB = True if os.environ.get("PDAGENTD_SCRUB_PII") and os.environ.get("PDAGENTD_SCRUB_PII").lower != 'false' else False

@app.route('/integration/<routing_key>/enqueue', methods=['POST'])
def enqueue_integration(routing_key):
	body = request.get_json(force=True)
	if not body:
		return "Bad request\n", 400

	if SCRUB:
		body = json.loads(scrub(json.dumps(body)))

	send_to_pd.delay(routing_key, body, destination_type="v1")
	return "Message enqueued\n"

@app.route('/x-ere/<routing_key>', methods=['POST'])
def enqueue_x_ere(routing_key):
	body = request.get_json(force=True)
	if not body:
		return "Bad request\n", 400

	if SCRUB:
		body = json.loads(scrub(json.dumps(body)))

	send_to_pd.delay(routing_key, body, destination_type="x-ere")
	return "Message enqueued\n"

@app.route('/v2/enqueue', methods=['POST'])
def enqueue_v2():
	body = request.get_json(force=True)
	if not body:
		return "Bad request\n", 400

	if not pd.is_valid_v2_payload(body):
		return "Invalid PD events v2 payload\n", 400

	try:
		routing_key = body['routing_key']
	except:
		return "No routing key found in payload\n", 400

	if not pd.is_valid_integration_key(routing_key):
		return "Invalid routing key found in payload\n", 400

	if SCRUB:
		body = json.loads(scrub(json.dumps(body)))

	send_to_pd.delay(routing_key, body, destination_type="v2")
	return "Message enqueued\n"
