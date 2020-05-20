# PDaltagent
A high-performance, easy-to-install alternative to pd-agent

## To just run in Docker from prebuilt images

* Install Docker and docker-compose
* Get the `docker-compose.yml` file from this repo and save it somewhere
* If you want PDaltagent to look for incidents in your domain and send webhooks, set `PD_API_TOKEN` and `WEBHOOK_DEST_URL` in `docker-compose.yml`
* In the same directory as the `docker-compose.yml` file, type: `docker-compose up -d`. This will run the `pdagentd` worker and a RabbitMQ broker in Docker.
* To send an event: `docker exec pdaltagent_pdagentd pd-send`
* To make it easier to send an event: `alias pd-send='docker exec pdaltagent_pdagentd pd-send'`
* Other interesting environment variables you can set include:
    * `SCRUB_PII` - attempt to scrub PII before sending events (see pdaltagent/scrubber.py for details)
    * `GET_ALL_LOG_ENTRIES` - generate additional webhooks for non-standard incident lifecycle events, like priority changes and responder requests (see PD documentation on incident log entries for the kinds of log entries that will be retrieved)
    * `POLLING_INTERVAL_SECONDS` - change the interval for log entry polling - the default is 10 seconds
    * `KEEP_ACTIVITY_SECONDS` - change the length of time that log entries are remembered in the activity store for deduplication - the default is 30 days

## Ways of sending events to PagerDuty through PDaltagent

* `docker exec pdaltagent_pdagentd pd-send` runs `pdsend.py` inside the Docker container, with `PD_EVENTS_BASE_URL` environment variable set to `http://localhost:5000`. `pdsend.py` just builds a PagerDuty event payload and sends it via HTTP/HTTPS POST to the base URL that is set in `PD_EVENTS_BASE_URL`.
* You can also copy `pdsend.py` outside the Docker container, and invoke it with an appropriate `PD_EVENTS_BASE_URL` set to point to the listening port on the `pdaltagent_pdagentd` Docker container
* If you have other tools sending events directly via HTTPS POST to `events.pagerduty.com`, you can change the beginning of the URL to point to HTTP on the listening port on the `pdaltagent_pdagentd` Docker container and leave the path the same, and the PDaltagent will enqueue the messages. This works for paths that look like `/integration/<routing_key>/enqueue`, `/x-ere/<routing_key>`, and `/v2/enqueue`

## To build a Docker image

* Install Docker
* Install [Poetry](https://python-poetry.org)
* Install the dependencies: `poetry install`
* Build the Python package (the Docker build needs it): `poetry build`
* Build the Docker image: `docker build --tag whatever .`

## To build a standalone package that can be installed via pip

* Install [Poetry](https://python-poetry.org)
* Install the dependencies: `poetry install`
* Build the Python package: `poetry build`
* The installable `.whl` file will be in the `dist/` directory
* You can install locally (wherever you have python3 + pip3 installed): `pip install ./PDaltagent-*.whl`
* Then you can run a worker by typing `pdagentd` and send an event by typing `pd-send`
* In this case you are responsible for creating a broker backend and passing it. Default backend is AMQP (probably RabbitMQ) running on localhost. This project uses [Celery](http://www.celeryproject.org) for queuing, so set the `CELERY_BROKER_URL` environment variable to wherever you have your RabbitMQ (or whatever) broker running

## To develop

* Install [Poetry](https://python-poetry.org)
* Install the dependencies: `poetry install`
* To start the worker: `poetry run pdagentd`
* To send an event: `poetry run pd-send`
* In this case you are still responsible for creating a broker backend and passing it 😀
