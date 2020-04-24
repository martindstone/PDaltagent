FROM alpine:latest
RUN apk add --no-cache python3 supervisor sqlite

RUN addgroup celery
RUN adduser --ingroup celery --disabled-password --no-create-home celery

WORKDIR /etc
COPY pdaltagent/scripts/supervisord.conf .

WORKDIR /tmp
COPY dist/PDaltagent*.whl .
RUN pip3 install ./PDaltagent*.whl
COPY pdaltagent/scripts/create_activity_store.sql .
RUN sqlite3 activity_store.db < create_activity_store.sql
RUN chown celery:celery activity_store.db

ENTRYPOINT supervisord -c /etc/supervisord.conf