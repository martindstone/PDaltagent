import pdaltagent.pd

class Plugin():
  """
  Default PDaltagent Plugin. You can have as many of these as you like.
  The class needs to be called Plugin and it can implement 3 different
  kinds of functionality:

    filter_events - to filter events on the way to PagerDuty
    filter_webhooks - to filter reconstructed webhooks from PagerDuty
    fetch_events - to go get events from somewhere and send them to PagerDuty at some interval

  This module will get imported inside the Python environment where PDaltagent is running. If
  you're running in Docker and you need to use other pip packages, use the `add_pip_pkg` command
  that's installed in /usr/local/bin. This installs pip packages in an include directory that's mounted at
  ./pdaltagent_pdagentd/plugins/lib outside the container (see the docker-compose.yml for details)
  """

  def __init__(self):
    """
    Do your plugin initialization here.

    If you implement a fetch_events method, PDaltagent will call it every `self.fetch_interval` seconds.
    If you don't set `self.fetch_interval`, it will default to PDAGENTD_POLLING_INTERVAL_SECONDS env var
    or 10 seconds if you haven't set that.
    Anyway, if a call to fetch_events takes longer than self.fetch_interval seconds to return, it
    will be aborted, so as to avoid multiple fetches running at once.

    `self.order` specifies the order in which this class's filter_event and filter_webhook
    methods will run, if you implement those. Lower comes before higher.
    """

    self.order = 100
    self.fetch_interval = 30

  def filter_event(self, event):
    """
    Filter events before sending to PagerDuty.

    You can have your function signature take args like:
      (event)
      (event, routing_key)
      (event, routing_key, destination_type)

    You can return:
      None, to indicate that event processing should stop and the event should not be sent at all
      A dict containing a valid v2 event (meaning the routing key and destination type will remain the same)
      A (dict, str) tuple containing a valid v2 event and a routing key
      A (dict, str, str) tuple containing event, routing key, destination type (one of "v2", "x-ere", "v1")
      A (dict, str, str, True) tuple indicating that the event should be sent, but no more filters should be run after this one
      You can set any of the strs in any of the tuples above to None to leave its value unchanged
    """
    return event

  def filter_webhook(self, webhook):
    """
    Filter webhooks before sending.

    You can have your function signature take args like:
      (webhook)
      (webhook, destination_url)

    You can return:
      None, to indicate that webhook processing should stop and the webhook should not be sent at all
      A dict of the webhook payload you want to send to the default configured URL (PDAGENTD_WEBHOOK_DEST_URL environment variable)
      A (dict, str) tuple containing the webhook payload and a new URL to send to
      A (dict, str, True) tuple indicating that the webhook should be sent, but no more filters should be run after this one
      You can set any of the strs in any of the tuples above to None to leave its value unchanged
    """
    return webhook

  def fetch_events(self):
    """
    Fetch events from somewhere to send to PagerDuty. You should return an array of dicts containing valid PagerDuty v2 Events.
    These events will be processed by any filter_events plugins that you have configured.
    """
    return []