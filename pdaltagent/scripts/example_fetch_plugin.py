import pdaltagent.pd
import requests

class Plugin():
  def __init__(self):
    self.fetch_interval = 30

  # Uncomment the method below to send a random cat fact to PagerDuty every 30 seconds!
  #
  # def fetch_events(self):
  #   """Get events from somewhere format them as PD v2 events
    
  #   Put your own PD (events v2 or event orchestration) routing key below
  #   """
  #   r = requests.get('https://meowfacts.herokuapp.com')
  #   fact = r.json()['data'][0]
  #   p = {
  #     'routing_key': 'YOUR_ROUTING_KEY_HERE',
  #     'event_action': 'trigger',
  #     'payload': {
  #       'summary': fact,
  #       'source': 'Cat Facts',
  #       'severity': 'critical',
  #     }
  #   }
  #   return [p]