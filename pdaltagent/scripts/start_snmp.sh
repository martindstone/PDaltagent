#!/bin/sh

if [ "${PDAGENTD_SNMP_ENABLED:-false}" = "true" ]; then
  exec pdagent-snmp
fi

echo "SNMP trap listener disabled; set PDAGENTD_SNMP_ENABLED=true to enable."
sleep infinity
