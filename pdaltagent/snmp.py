import logging
import os
from typing import Dict

import pdaltagent.pd as pd
from pdaltagent.config import env_flag
from pdaltagent.tasks import send_to_pd

try:
    from pysnmp.carrier.asyncore.dgram import udp
    from pysnmp.entity import config, engine
    from pysnmp.entity.rfc3413 import ntfrcv

    SNMP_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime guard only
    SNMP_AVAILABLE = False

logger = logging.getLogger(__name__)


def _as_details(var_binds) -> Dict[str, str]:
    return {str(name): str(val) for name, val in var_binds}


def _trap_oid(var_binds) -> str:
    for name, val in var_binds:
        if str(name).endswith("1.3.6.1.6.3.1.1.4.1.0"):
            return str(val)
    return str(var_binds[0][0]) if var_binds else "unknown"


def _build_payload(
    routing_key: str,
    source: str,
    severity: str,
    summary_template: str,
    var_binds,
) -> Dict:
    details = _as_details(var_binds)
    trap_oid = _trap_oid(var_binds)
    summary = summary_template.format(trap_oid=trap_oid, source=source)
    return {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "source": source,
            "severity": severity,
            "custom_details": details,
        },
    }


def _trap_callback(snmp_engine, state_reference, context_engine_id, context_name, var_binds, ctx):
    transport_domain, transport_address = snmp_engine.msgAndPduDsp.getTransportInfo(state_reference)
    source = f"{transport_address[0]}:{transport_address[1]}"
    payload = _build_payload(
        routing_key=ctx["routing_key"],
        source=source,
        severity=ctx["severity"],
        summary_template=ctx["summary_template"],
        var_binds=var_binds,
    )
    logger.info("Received SNMP trap from %s with %d bindings", source, len(var_binds))
    send_to_pd.delay(ctx["routing_key"], payload, base_url=ctx["base_url"], destination_type="v2")


def run_server():
    if not SNMP_AVAILABLE:
        raise RuntimeError(
            "SNMP trap support requires the pysnmp-lextudio extra. "
            "Install with `pip install pdaltagent[snmp]`."
        )

    routing_key = os.getenv("PDAGENTD_SNMP_ROUTING_KEY")
    if not routing_key or not pd.is_valid_integration_key(routing_key):
        raise RuntimeError("PDAGENTD_SNMP_ROUTING_KEY must be set to a valid PagerDuty routing key.")

    host = os.getenv("PDAGENTD_SNMP_HOST", "0.0.0.0")
    port = int(os.getenv("PDAGENTD_SNMP_PORT", "9162"))
    community = os.getenv("PDAGENTD_SNMP_COMMUNITY", "public")
    severity = os.getenv("PDAGENTD_SNMP_SEVERITY", "error")
    summary_template = os.getenv("PDAGENTD_SNMP_SUMMARY", "SNMP trap {trap_oid} from {source}")
    base_url = os.getenv("PDAGENTD_SNMP_EVENTS_URL") or os.getenv("PDSEND_EVENTS_BASE_URL") or "https://events.pagerduty.com"

    snmp_engine = engine.SnmpEngine()
    config.addTransport(
        snmp_engine,
        udp.domainName,
        udp.UdpTransport().openServerMode((host, port)),
    )
    config.addV1System(snmp_engine, "pdaltagent-snmp", community)
    config.addVacmUser(snmp_engine, 2, "pdaltagent-snmp", "noAuthNoPriv", readSubTree=(1, 3, 6, 1, 4, 1))

    ctx = {
        "routing_key": routing_key,
        "severity": severity,
        "summary_template": summary_template,
        "base_url": base_url,
    }
    ntfrcv.NotificationReceiver(snmp_engine, lambda *args: _trap_callback(*args, ctx))

    logger.info("Listening for SNMP traps on %s:%s (community=%s)", host, port, community)
    snmp_engine.transportDispatcher.jobStarted(1)
    try:
        snmp_engine.transportDispatcher.runDispatcher()
    finally:
        snmp_engine.transportDispatcher.closeDispatcher()


def main():
    logging.basicConfig(level=logging.INFO)
    if not env_flag("PDAGENTD_SNMP_ENABLED"):
        logger.info("SNMP trap listener disabled (set PDAGENTD_SNMP_ENABLED=true to enable)")
        return
    run_server()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
