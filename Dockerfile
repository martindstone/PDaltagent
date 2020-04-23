FROM alpine:latest
RUN apk add --no-cache python3

RUN addgroup celery
RUN adduser --ingroup celery --disabled-password --no-create-home celery

WORKDIR /tmp
COPY dist/PDaltagent*.whl .
RUN pip3 install ./PDaltagent*.whl

ENTRYPOINT celery worker -A pdaltagent.tasks -E -l info --uid=celery --gid=celery