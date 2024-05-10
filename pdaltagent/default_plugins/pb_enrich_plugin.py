from pdaltagent.config import MONGODB_URL
from pdaltagent.enrichment import Enrichment
from pymongo import MongoClient
import datetime
import json
import traceback

prepend_path = "payload.custom_details."

class Plugin:
    def __init__(self):
        self.order = 100
        # default refresh time is 1 hour
        self.refresh_time = datetime.timedelta(hours=1)

        # add k/v pairs to the event for debugging enrichment
        self.debug_enrichment = True

        # set to True to enable debug logging and add messages to the event
        self.debug = True

        self.enrich = Enrichment(
            MONGODB_URL,
            debug=self.debug,
            broken_regex=True,
            prepend_path=prepend_path,
            tz="UTC",
        )

        self.tracking_coll = self.enrich.db["_enrich_tracking"]
        # set ttl of one day on documents in tracking_coll
        self.tracking_coll.create_index(
            "created_at", expireAfterSeconds=86400, background=True
        )

        self.last_loaded_time = datetime.datetime.now(datetime.timezone.utc)

    def tracking_fields(self, event):
        r = {}
        for k in [
            "client",
            "client_url",
            "payload.source",
            "payload.summary",
            "payload.custom_details.source_system",
        ]:
            t = self.enrich.get_value_at_path(event, k)
            if t:
                r[k.replace('.', '_')] = t
        return r

    def filter_event(self, event):
        tracking_info = {
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "before": json.loads(json.dumps(event)),
        }
        # check if last loaded is more than refresh time before now
        now = datetime.datetime.now(datetime.timezone.utc)
        if now - self.last_loaded_time > self.refresh_time:
            print("Refreshing enrichment data from MongoDB...")
            self.enrich.load_from_mongo()
            self.last_loaded_time = now

        try:
            event = self.enrich.enrich_event(event, debug_enrichment=self.debug_enrichment)
            (is_in_maint, maints_applied) = self.enrich.is_in_maint(event)
            self.enrich.set_value_at_path(
                event, "payload.custom_details.is_in_maint", is_in_maint
            )
            if is_in_maint and self.debug_enrichment:
                # translate timestamps in start and end to human readable and add to event
                friendly_maints_applied = []
                for maint in maints_applied:
                    friendly_maints_applied.append({
                        "start": self.enrich.timestamp_to_human(maint["start"]),
                        "end": self.enrich.timestamp_to_human(maint["end"]),
                        "maintenance_key": maint["maintenance_key"],
                        "name": maint["name"],
                        "frequency": maint["frequency"],
                        "frequency_data": maint["frequency_data"],
                    })
                self.enrich.set_value_at_path(
                    event,
                    "payload.custom_details.maints_applied",
                    friendly_maints_applied,
                )
            event = self.enrich.remove_falsy_values_from_object(event)
            messages = self.enrich.get_value_at_path(event, "payload.custom_details.messages")
            if isinstance(messages, list):
                tracking_info["messages"] = messages
                del event["payload"]["custom_details"]["messages"]
            tracking_info["after"] = json.loads(json.dumps(event))
            tracking_info.update(self.tracking_fields(event))
            self.tracking_coll.insert_one(tracking_info)
        except Exception as e:
            print(f"Error enriching event: {e}")
            traceback.print_exc()
            return event
        return event
