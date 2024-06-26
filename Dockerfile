FROM alpine:latest
RUN apk add --no-cache bash python3=3.12.3-r1 py3-pip=24.0-r2 py3-wheel=0.42.0-r1 supervisor openssl curl nodejs net-snmp

RUN addgroup celery
RUN adduser --ingroup celery --disabled-password --no-create-home celery

WORKDIR /etc
COPY pdaltagent/scripts/supervisord.conf .
COPY pdaltagent/scripts/run_supervisord.sh .
RUN chmod +x run_supervisord.sh

COPY pdaltagent/scripts/add_pip_pkg /usr/local/bin
RUN chmod +x /usr/local/bin/add_pip_pkg

WORKDIR /etc/pdagentd/ssl
RUN openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 3650 -subj "/C=US/ST=CA/L=San Francisco/CN=pagerduty.com"

WORKDIR /tmp
COPY dist/pdaltagent-0.5.0*.whl .
RUN pip3 install ./pdaltagent-0.5.0*.whl --break-system-packages

ENTRYPOINT /etc/run_supervisord.sh
