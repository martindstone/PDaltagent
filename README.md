# PDaltagent

A high-performance, easy-to-install alternative to [PagerDuty Agent](https://www.pagerduty.com/docs/guides/agent-install-guide/)

## Why PDaltagent?

I originally developed PDaltagent to provide a command-line compatible alternative to PagerDuty Agent that would perform better under heavy load, but it does other stuff as well. 

### Situations where you might want to use PDaltagent:

* If PagerDuty Agent isn't performing well when you are sending large volumes of events. Either events are getting stuck/delayed, or perhaps queued events and log messages are taking up a lot of space in your filesystem. PDaltagent uses RabbitMQ for queuing rather than a file-based queue, so it is more efficient at higher event volumes. It also does concurrency (faster event delivery) and automatic retry (more reliable event delivery) with exponential backoff.
* If you have systems that want to send events to PagerDuty but they are behind a firewall and can't make outbound HTTPS connections. PDaltagent can run on one central system with outbound HTTPS access and listen for PagerDuty events over HTTPS on your internal network, so that internal hosts can post events to a central location in your own network for queuing and delivery.
* If if you have systems that know how to send events to PagerDuty but don't have the ability to retry. Monitoring systems like AppDynamics and Splunk know how to send HTTPS POSTs, but if an internet connection isn't available when the event is produced, it may not be delivered. You can configure these systems to send events to PDaltagent instead of sending directly to PagerDuty, to implement a queuing layer that will improve reliability in case of internet outages.
* If you have systems that don't know how to send events to PagerDuty, or that want to send events using protocols other than HTTPS. For example, PDaltagent can be modified to listen to SNMP traps and send them to PagerDuty as events over HTTPS.
* If you want to manipulate the content of messages before they are sent to PagerDuty, for example to enrich events with information from a CMDB, or mask sensitive data. This is done by writing plugins, which are simply Python classes that implement the changes you want to make. Check out [the default plugin](pdaltagent/scripts/default_plugin.py) for some documentation on writing plugins, and [a simple practical example plugin](pdaltagent/scripts/example_filter_plugin.py).
* If you have systems that want to receive webhooks from PagerDuty but are behind a firewall that can't allow inbound HTTPS. PDaltagent can poll PagerDuty log entries and send PagerDuty webhooks to your systems from inside your network.
* Just for fun. This is how people have fun, right?

### Situations where you won't want to use PDaltagent:

* If you need to be absolutely certain that events will be delivered to PagerDuty in the order they were produced, PDaltagent probably isn't for you. It makes a good effort to preserve the overall order of messages, but when events are sent very close together in time, their delivery order can sometimes be changed. This case is probably rare, but if it's important it's probably really important.
* If you are prohibited from running open source software in your network, or need a vendor-supported solution. PDaltagent is open source software and is not supported by PagerDuty.
* If you just want a turnkey solution and don't want to understand how it works, you probably won't be happy with PDaltagent.

Okay, here's how you can get started:

## To just run in Docker from prebuilt images

* Install Docker and docker-compose
* Get the [Docker Compose YAML](./docker-compose.yml) file from this repo and save it in a new directory.
* If you want PDaltagent to look for incidents in your domain and send webhooks, set `PDAGENTD_API_TOKEN` and `PDAGENTD_WEBHOOK_DEST_URL` in `docker-compose.yml`; this is totally optional and not needed if you just want to use PDaltagent to send events to PagerDuty.
* In the same directory as the `docker-compose.yml` file, type: `docker-compose up -d`. This will run the `pdagentd` worker and a RabbitMQ broker in Docker.
* Take a look inside the `docker-compose.yml` file to see some other interesting environment variables you can set.

## What you get when you run using Docker Compose

* When you run PDaltagent using the Docker Compose in this repo, you will get four running containers:
    * `pdaltagent_pdagentd` is the container that is running the queue consumers and the HTTPS listener. It also has [PagerDuty CLI](https://github.com/martindstone/pagerduty-cli) installed for your convenience.
    * `pdaltagent_rabbitmq` is the container that is running the RabbitMQ backend for Celery. You can access the Rabbit management interface at `http://your_pdaltagent_host:15672`. See or change the username and password in docker-compose.yml.
    * `pdaltagent_mongo` is the container running MongoDB. PDaltagent uses Mongo to hold recently seen log entries when polling for webhooks, but you can also use it in your plugins.
    * `pdaltagent_mongo-express` is the container runing [Mongo-Express](https://github.com/mongo-express/mongo-express), which is a simple web UI for managing data stored in Mongo. See docker-compose.yml for the port, username and password. You can remove this container if you don't want to use Mongo-Express.

* Docker Compose will also create a directory called `pdaltagent_pdagentd` in the current directory when you run it. This directory has the following subdirectories:
    * `plugins` is where you put plugins that you write. There are a couple of example plugins added to this directory when it is first created. You can read these to find out how to write plugins, or just ignore them; they are disabled by default.
    * `plugin-lib` is where you install any additional libraries that your plugins might need. There's a convenience script called `add_pip_pkg` in the pdaltagent_pdagentd container that installs pip packages to the correct location for you. To use it, for example, to install Faker, you can type `docker exec pdaltagent_pdagentd add_pip_pkg faker`
    * `mongo_data` is where Mongo will keep its data. You shouldn't need to mess with it, but if you want you can back it up or mount a network volume there, etc.

* pdagentd will listen for events on port 8080 for cleartext HTTP and on port 8443 for HTTPS. You can change this by changing the mapped ports in the pdagentd section of docker-compose.yml
* By default, the pdagentd listener uses a self-signed cert and key for HTTPS. This can cause warnings and failures on some clients, unless you tell them to skip certificate verification. If you cant to use your own cert and key, see the example in docker-compose.yml to create a bindmoint for `/etc/pdagentd/ssl/cert.pem` and `/etc/pdagentd/ssl/key.pem`.
* If you want to change the services that are run in the container, see the example in docker-compose.yml to create a bindmount for `/etc/supervisord.conf`.

## How to send events to PagerDuty through PDaltagent

* If you have tools that want to send events directly via HTTPS POST to `events.pagerduty.com`, you can change the beginning of the URL to point to HTTP/HTTPS on the listening ports on the `pdaltagent_pdagentd` Docker container and leave the path the same, and the PDaltagent will enqueue the messages. This works for paths that look like `/integration/<routing_key>/enqueue`, `/x-ere/<routing_key>`, and `/v2/enqueue`. For example, if you have an event that you send to `https://events.pagerduty.com/v2/enqueue`, and your pdagentd is listening for HTTPS on port 8443 on host 10.0.0.10, you can send the same event to `https://10.0.0.10:8443/v2/enqueue`.

## Other ways to send events to PagerDuty through PDaltagent

If you want to send events to PagerDuty without doing an HTTPS POST to the pdagentd listener, here are some other options:

* If you want to poll some system or run some logic on a schedule and generate events based on that logic, you can write a PDaltagent plugin that implements the `fetch_events` method. PDaltagent will run your `fetch_events` method at the interval you specify, and if it returns events, it will send those events to PagerDuty. Take a look at [the default plugin](pdaltagent/scripts/default_plugin.py) for documentation on how to write this.
* `docker exec pdaltagent_pdagentd pd-send` runs `pdsend.py` inside the Docker container, with `PDSEND_EVENTS_BASE_URL` environment variable set to `https://localhost:8443`, which is where pdagentd listens for HTTPS POSTs of PagerDuty events. `pdsend.py` just builds a PagerDuty event payload and sends it via HTTP/HTTPS POST to the base URL that is set in `PDSEND_EVENTS_BASE_URL`.
* You can also copy `pdsend.py` outside the Docker container, and invoke it with `PDSEND_EVENTS_BASE_URL` set to point to the listening port on the `pdaltagent_pdagentd` Docker container - like `https://your_host_name_or_ip:8443`. The Docker image ships with a self-signed certificate. If you are using a self-signed cert, set `PDSEND_SKIP_CERT_VERIFY=true` to skip certificate verification. Or you can set it to connect to cleartext HTTP on port 8080.

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
* In this case you are responsible for creating a broker backend and passing it. Default backend is AMQP (probably RabbitMQ) running on localhost. This project uses [Celery](http://www.celeryproject.org) for queuing, so set the `CELERY_BROKER_URL` environment variable to wherever you have your RabbitMQ (or whatever) broker running. Take a look at [the Docker Compose YAML file](./docker-compose.yml) for details on these environment variables.

## To develop

* Install [Poetry](https://python-poetry.org)
* Install the dependencies: `poetry install`
* To start the worker: `poetry run pdagentd`
* To send an event: `poetry run pd-send`
* In this case you are still responsible for creating a broker backend and passing it 😀
