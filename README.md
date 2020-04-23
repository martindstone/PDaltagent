# PDaltagent
A high-performance, easy-to-install alternative to pd-agent

## To just run in Docker from prebuilt images

* Install Docker and docker-compose
* Get the `docker-compose.yml` file from this repo and save it somewhere
* In the same directory as the `docker-compose.yml` file, type: `docker-compose up -d`. This will run the `pdagentd` worker and a RabbitMQ broker in Docker.
* To send an event: `docker exec pdaltagent_pdagentd pd-send`
* To make it easier to send an event: `alias pd-send='docker exec pdaltagent_pdagentd pd-send'`

## To develop:

* Install [Poetry](https://python-poetry.org)
* Install the dependencies: `poetry install`
* To start the worker: `poetry run pdagentd`
* To send an event: `poetry run pd-send`

## To build a standalone package that can be installed via pip

* Build the package: `poetry build`
* The installable `.whl` file will be in the `dist/` directory
* You can install locally (wherever you have python3 + pip3 installed): `pip install ./PDaltagent-*.whl`
* Then you can run a worker by typing `pdagentd` and send an event by typing `pd-send`
* In this case you are responsible for creating a broker backend and passing it. Default backend is AMQP (probably RabbitMQ) running on localhost. This project uses [Celery](http://www.celeryproject.org) for queuing, so set the `CELERY_BROKER_URL` environment variable to wherever you have your RabbitMQ (or whatever) broker running

## To build a Docker image

* Install Docker
* Build the Python package (the Docker build needs it): `poetry build`
* Build the Docker image: `docker build --tag whatever .`
