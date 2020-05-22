# PDaltagent

A high-performance, easy-to-install alternative to [PagerDuty Agent](https://www.pagerduty.com/docs/guides/agent-install-guide/)

## Why PDaltagent?

I originally developed PDaltagent to provide a command-line compatible alternative to PagerDuty Agent that would perform better under heavy load, but it does other stuff as well. 

### Situations where you might want to use PDaltagent:

* If PagerDuty Agent isn't performing well when you are sending large volumes of events. Either events are getting stuck/delayed, or perhaps queued events and log messages are taking up a lot of space in your filesystem. PDaltagent uses RabbitMQ for queuing rather than a file-based queue, so it is more efficient at higher event volumes. It also does concurrency (faster event delivery) and automatic retry (more reliable event delivery) with exponential backoff.
* If you have systems that want to send events to PagerDuty but they are behind a firewall and can't make outbound HTTPS connections. PDaltagent can run on one central system with outbound HTTPS access and you can distribute the send command to your firewalled systems, so that they can post payloads to a central location in your own network for queuing and delivery.
* If if you have systems that know how to send events to PagerDuty but don't have the ability to retry. Monitoring systems like AppDynamics and Splunk know how to send HTTPS POSTs, but if an internet connection isn't available when the event is produced, it may not be delivered. You can configure these systems to send events to PDaltagent instead of sending directly to PagerDuty, to implement a queuing layer that will improve reliability in case of internet outages.
* If you want to manipulate the content of messages before they are sent to PagerDuty, for example to mask sensitive data. Check out the `SCRUB_PII` environment setting for a simple example.
* If you have systems that want to receive webhooks from PagerDuty but are behind a firewall that can't allow inbound HTTPS. PDaltagent can poll PagerDuty log entries and send PagerDuty webhooks to your systems from inside your network.
* Just for fun. This is how people have fun, right?

### Situations where you won't want to use PDaltagent:

* If you need to be absolutely certain that events will be delivered to PagerDuty in the order they were produced, PDaltagent probably isn't for you. It makes a good effort to preserve the overall order of messages, but when events are sent very close together in time, their delivery order can sometimes be changed. This case is probably rare, but if it's important it's probably really important.

Okay, here's how you can get started:

## To just run in Docker from prebuilt images

* Install Docker and docker-compose
* Get the `docker-compose.yml` file from this repo and save it somewhere
* If you want PDaltagent to look for incidents in your domain and send webhooks, set `PDAGENTD_API_TOKEN` and `PDAGENTD_WEBHOOK_DEST_URL` in `docker-compose.yml`
* In the same directory as the `docker-compose.yml` file, type: `docker-compose up -d`. This will run the `pdagentd` worker and a RabbitMQ broker in Docker.
* To send an event: `docker exec pdaltagent_pdagentd pd-send`
* To make it easier to send an event: `alias pd-send='docker exec pdaltagent_pdagentd pd-send'`
* Other interesting environment variables you can set include:
    * `PDAGENTD_SCRUB_PII` - attempt to scrub PII before sending events (see pdaltagent/scrubber.py for details)
    * `PDAGENTD_GET_ALL_LOG_ENTRIES` - generate additional webhooks for non-standard incident lifecycle events, like priority changes and responder requests (see PD documentation on incident log entries for the kinds of log entries that will be retrieved)
    * `PDAGENTD_POLLING_INTERVAL_SECONDS` - change the interval for log entry polling - the default is 10 seconds
    * `PDAGENTD_KEEP_ACTIVITY_SECONDS` - change the length of time that log entries are remembered in the activity store for deduplication - the default is 30 days

## Ways of sending events to PagerDuty through PDaltagent

* `docker exec pdaltagent_pdagentd pd-send` runs `pdsend.py` inside the Docker container, with `PDSEND_EVENTS_BASE_URL` environment variable set to `https://localhost:8443`, which is where pdagentd listens for HTTPS POSTs of PagerDuty events. `pdsend.py` just builds a PagerDuty event payload and sends it via HTTP/HTTPS POST to the base URL that is set in `PDSEND_EVENTS_BASE_URL`.
* You can also copy `pdsend.py` outside the Docker container, and invoke it with `PDSEND_EVENTS_BASE_URL` set to point to the listening port on the `pdaltagent_pdagentd` Docker container - like `https://your_host_name_or_ip:8443`. The Docker image ships with a self-signed certificate. If you are using a self-signed cert, set `PDSEND_SKIP_CERT_VERIFY=true` to skip certificate verification. Or you can set it to connect to cleartext HTTP on port 8080.
* If you have other tools that want to send events directly via HTTPS POST to `events.pagerduty.com`, you can change the beginning of the URL to point to HTTP/HTTPS on the listening ports on the `pdaltagent_pdagentd` Docker container and leave the path the same, and the PDaltagent will enqueue the messages. This works for paths that look like `/integration/<routing_key>/enqueue`, `/x-ere/<routing_key>`, and `/v2/enqueue`

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
