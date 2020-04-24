import re
import json
import requests
import datetime

# Uncomment the section below for low-level HTTPS debugging
# import logging
# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

BASE_URL = 'https://api.pagerduty.com'

def auth_header_for_token(token):
    if re.search("^[0-9a-f]{64}$", token):
        return f"Bearer {token}"
    else:
        return f"Token token={token}"

def url_for_routing_key(routing_key):
    if routing_key.startswith("R"):
        return f"https://events.pagerduty.com/x-ere/{routing_key}"
    else:
        return "https://events.pagerduty.com/v2/enqueue"

def is_classic_integration_key(str):
    regex = re.compile("^[0-9a-f]{32}$", re.IGNORECASE)
    return regex.match(str)

def is_rules_engine_key(str):
    regex = re.compile("^R[0-9A-Z]{31}$", re.IGNORECASE)
    return regex.match(str) 

def is_valid_integration_key(str):
    return (is_classic_integration_key(str) or is_rules_engine_key(str))

def send_v2_event(routing_key, payload):
    url = url_for_routing_key(routing_key)

    headers = {
        "Content-Type": "application/json"
    }
    req = requests.Request(
        method='POST',
        url=url,
        headers=headers,
        json=payload
    )

    prepped = req.prepare()
    response = requests.Session().send(prepped)
    response.raise_for_status()
    if len(response.content) > 0:
        return response.json()
    else:
        return None

def request(token=None, endpoint=None, method="GET", params=None, data=None, addheaders=None):

    if not endpoint or not token:
        return None


    url = '/'.join([BASE_URL, endpoint])
    headers = {
        "Accept": "application/vnd.pagerduty+json;version=2",
        "Authorization": auth_header_for_token(token)
    }

    if data != None:
        headers["Content-Type"] = "application/json"

    if addheaders:
        headers.update(addheaders)

    req = requests.Request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=data
    )

    prepped = req.prepare()
    response = requests.Session().send(prepped)
    response.raise_for_status()
    if len(response.content) > 0:
        return response.json()
    else:
        return None

def fetch(token=None, endpoint=None, params=None):
    my_params = {}
    if params:
        my_params = params.copy()

    fetched_data = []
    offset = 0
    array_name = endpoint.split('/')[-1]
    while True:
        try:
            r = request(token=token, endpoint=endpoint, params=my_params)
            fetched_data.extend(r[array_name])
        except:
            print(f"Oops! {r}")

        if not (("more" in r) and r["more"]):
            break
        offset += r["limit"]
        my_params["offset"] = offset
    return fetched_data

def fetch_incidents(token=None, params={"statuses[]": ["triggered", "acknowledged"]}):
    return fetch(token=token, endpoint="incidents", params=params)

def fetch_users(token=None, params=None):
    return fetch(token=token, endpoint="users", params=params)

def fetch_escalation_policies(token=None, params=None):
    return fetch(token=token, endpoint="escalation_policies", params=params)

def fetch_services(token=None, params=None):
    return fetch(token=token, endpoint="services", params=params)

def fetch_schedules(token=None, params=None):
    return fetch(token=token, endpoint="schedules", params=params)

def fetch_teams(token=None, params=None):
    return fetch(token=token, endpoint="teams", params=params)

def fetch_log_entries(token=None, params=None):
    fetch_params = {
        'since': (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).replace(microsecond=0).isoformat(),
        'until': datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
        'is_overview': 'true',
        'include[]': ['incidents', 'services']
    }
    if params:
        fetch_params.update(params)
    return fetch(token=token, endpoint="log_entries", params=fetch_params)

def ile_to_webhook(ile):
    event = ile['type'].split('_')[0]
    short_service = ile['incident']['service']
    long_service = ile['service']
    long_incident = ile['incident']
    short_incident = dict((k, long_incident[k]) for k in ["id", "type", "summary", "self", "html_url"])
    short_incident['type'] = 'incident_reference'

    long_incident['service'] = long_service

    webhook_log_entry = ile
    webhook_log_entry['incident'] = short_incident
    webhook_log_entry['service'] = short_service
    message = {
        "event": f"incident.{event}",
        "log_entries": [
            ile
        ],
        "incident": long_incident
    }
    webhook = {
        "messages": [
            message
        ]
    }
    return webhook