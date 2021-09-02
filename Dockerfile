FROM alpine:latest
RUN apk add --no-cache python3 py3-pip supervisor sqlite openssl

RUN addgroup celery
RUN adduser --ingroup celery --disabled-password --no-create-home celery

WORKDIR /etc
COPY pdaltagent/scripts/supervisord.conf .

WORKDIR /etc/pdagentd/ssl
RUN openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650 -subj "/C=US/ST=CA/L=San Francisco/CN=pagerduty.com"

WORKDIR /tmp
COPY dist/PDaltagent*.whl .
RUN pip3 install ./PDaltagent-0.2.0*.whl
COPY pdaltagent/scripts/create_activity_store.sql .
RUN sqlite3 activity_store.db < create_activity_store.sql
RUN chown celery:celery activity_store.db

ENTRYPOINT supervisord -c /etc/supervisord.conf