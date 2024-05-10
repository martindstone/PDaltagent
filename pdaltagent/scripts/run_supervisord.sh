#!/bin/sh

export SUPERVISOR_USER="${SUPERVISOR_USER:-pdaltagent}"
export SUPERVISOR_PASS="${SUPERVISOR_PASS:-pdaltagent}"

supervisord -c /etc/supervisord.conf
