import pdaltagent.plugins
import pdaltagent.pd
import importlib
import pkgutil
import inspect
import logging
import sys
import os
import validators
from pathlib import Path

from celery.app.defaults import DEFAULT_PROCESS_LOG_FMT
from celery.utils.log import get_task_logger

class PluginHost:
  @staticmethod
  def methodname(method):
    if inspect.ismethod(method):
      return inspect.getmodule(method).__name__
    elif isinstance(method, dict) and 'method' in method and inspect.ismethod(method['method']):
      return inspect.getmodule(method['method']).__name__
    else:
      return '(unknown)'


  def __init__(self, debug=False):
    modlibpath = str(Path(pdaltagent.__path__[0], 'plugin-lib').resolve().absolute())
    if not modlibpath in sys.path:
      sys.path.append(modlibpath)

    loglevel = logging.INFO
    if debug or os.getenv('PDAGENTD_DEBUG'):
      loglevel = logging.DEBUG
    logging.basicConfig(
      format=DEFAULT_PROCESS_LOG_FMT,
      level = loglevel
    )
    self.logger = get_task_logger(__name__)

    self.methods = {
      'filter_event': [],
      'filter_webhook': [],
      'fetch_events': [],
    }
    self.logger.debug('PluginHost init loading plugins...')
    self.load_plugins()
  

  def load_plugins(self):
    """Load all the plugins in the pdaltagent.plugins namespace"""

    self.modnames = [x.name for x in pkgutil.iter_modules(pdaltagent.plugins.__path__, pdaltagent.plugins.__name__ + '.')]
    self.logger.debug(f"Found {len(self.modnames)} module names: {', '.join(self.modnames)}")
    self.modules = []
    for modname in self.modnames:
      try:
        self.modules.append(importlib.import_module(modname))
      except Exception as e:
        self.logger.error(f"Couldn't import {modname}: {e}")

    self.instances = []
    for module in self.modules:
      try:
        self.instances.append(module.Plugin())
      except Exception as e:
        self.logger.error(f"Couldn't instantiate Plugin class of module {module.__name__}: {e}")
    self.instances.sort(key=lambda x: (x.order if isinstance(getattr(x, 'order', None), int) else 999))

    for instance in self.instances:
      for method_type in self.methods.keys():
        method = getattr(instance, method_type, None)
        if inspect.ismethod(method):
          if method_type == 'fetch_events':
            self.methods[method_type].append({
              'method': method,
              'fetch_interval': getattr(method.__self__, 'fetch_interval', 10)
            })
          else:
            self.methods[method_type].append(method)
    for method_type in self.methods.keys():
      self.logger.debug(f"Loaded {method_type} methods from {len(self.methods[method_type])} modules ({', '.join([self.methodname(x) for x in self.methods[method_type]])})")


  def unload_plugins(self):
    """Unload all the loaded plugins"""

    for method_type in self.methods.keys():
      self.methods[method_type] = []
    del self.instances, self.modules, self.modnames
    for modname in [x for x in sys.modules.keys() if x.startswith('pdaltagent.plugins.')]:
      del sys.modules[modname]


  def reload_plugins(self):
    """Reload plugins"""

    self.unload_plugins()
    self.load_plugins()


  def call_filter_event_method(self, method, event, routing_key=None, destination_type="v2"):
    """Call filter event method which may have a few different signatures and return a few different types,
    and return a standard dict

    Args:
        method (function): the method to call
        event (dict): the event to filter
        routing_key (str, optional): the routing key. Defaults to None.
        destination_type (str, optional): the type of PD integration - x-ere, v1 or v2. Defaults to "v2".

    Raises:
        ValueError: if the filter method signature is invalid
        ValueError: if the filter method returns an invalid value

    Returns:
        dict: a dict with keys "event", "routing_key", "destination_type", "stop"
    """

    _event = dict(event)
    num_params = len(inspect.signature(method).parameters)
    if num_params == 1:
      r = method(_event)
    elif num_params == 2:
      r = method(_event, routing_key)
    elif num_params == 3:
      r = method(_event, routing_key, destination_type)
    else:
      raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} takes an invalid number of arguments. It should take 1-3")

    if r is None:
      return None

    ret = {
      'event': None,
      'routing_key': routing_key,
      'destination_type': destination_type,
      'stop': False,
    }

    if isinstance(r, dict):
      ret['event'] = r
      return ret
    if isinstance(r, tuple):
      if not 1 <= len(r) <= 4:
        raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} returned invalid value {r}. Should return a (event, routing_key?, destination_type?, stop?) tuple.")
      if not isinstance(r[0], dict):
        raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} returned a tuple with invalid event {r[0]}. The first element of the tuple should be an event dict.")
      ret['event'] = r[0]
      if len(r) == 1:
        return ret
      if r[1] is not None and not pdaltagent.pd.is_valid_integration_key(r[1]):
        raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} returned a tuple with invalid routing key {r[1]}. The second element of the tuple should be a routing key or None.")
      ret['routing_key'] = r[1] or ret['routing_key']
      if len(r) == 2:
        return ret
      if r[2] is not None and not isinstance(r[2], str):
        raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} returned a tuple with invalid destination type {r[2]}. The third element of the tuple should be a string or None.")
      ret['destination_type'] = r[2] or ret['destination_type']
      if len(r) == 3:
        return ret
      if r[3]:
        ret['stop'] = True
      return ret

    raise ValueError(f"Plugin.filter_event method of {inspect.getmodule(method).__name__} returned invalid value of type {type(r).__name__}. Should return a dict, tuple or None")


  def call_filter_webhook_method(self, method, webhook, destination_url=None):
    """Call filter webhook method which may have a few different signatures and return a few different types,
    and return a standard dict

    Args:
        method (function): the method to call
        webhook (dict): the webhook to filter
        routing_key (str, optional): the routing key. Defaults to None.
        destination_type (str, optional): the type of PD integration - x-ere, v1 or v2. Defaults to "v2".

    Raises:
        ValueError: if the filter method signature is invalid
        ValueError: if the filter method returns an invalid value

    Returns:
        dict: a dict with keys "webhook", "destination_url", "stop"
    """
    _webhook = dict(webhook)
    num_params = len(inspect.signature(method).parameters)
    if num_params == 1:
      r = method(_webhook)
    elif num_params == 2:
      r = method(_webhook, destination_url)
    else:
      raise ValueError(f"Plugin.filter_webhook method of {inspect.getmodule(method).__name__} takes an invalid number of arguments. It should take 1-2")

    if r is None:
      return None

    ret = {
      'webhook': None,
      'destination_url': destination_url,
      'stop': False,
    }

    if isinstance(r, dict):
      ret['webhook'] = r
      return ret
    if isinstance(r, tuple):
      if not 1 <= len(r) <= 3:
        raise ValueError(f"Plugin.filter_webhook method of {inspect.getmodule(method).__name__} returned invalid value {r}. Should return a (webhook, destination_url?, stop?) tuple.")
      if not isinstance(r[0], dict):
        raise ValueError(f"Plugin.filter_webhook method of {inspect.getmodule(method).__name__} returned a tuple with invalid webhook {r[0]}. The first element of the tuple should be a webhook payload dict.")
      ret['webhook'] = r[0]
      if len(r) == 1:
        return ret
      if r[1] is not None and (not isinstance(r[1], str) or validators.url(r[1]) != True):
        raise ValueError(f"Plugin.filter_webhook method of {inspect.getmodule(method).__name__} returned a tuple with invalid destination url {r[1]}. The second element of the tuple should be a destination url or None.")
      ret['destination_url'] = r[1] or ret['destination_url']
      if len(r) == 2:
        return ret
      if r[2]:
        ret['stop'] = True
      return ret

    raise ValueError(f"Plugin.filter_webhook method of {inspect.getmodule(method).__name__} returned invalid value of type {type(r).__name__}. Should return a dict, tuple or None")

  def filter_event(self, event, routing_key=None, destination_type="v2"):
    """call all the filter event methods in order and return the result or None to suppress the event

    Args:
        event (dict): the event to filter
        routing_key (str, optional): the routing key. Defaults to None.
        destination_type (str, optional): the type of PD integration - x-ere, v1 or v2. Defaults to "v2".

    Returns:
        tuple: a tuple with the new event, routing key and destination type, or None if suppressed
    """

    if not isinstance(event, dict):
      self.logger.error(f"PluginHost.filter_event method called with an invalid value {event}. Call this method with a dict.")
      return None

    _event = dict(event)
    _routing_key = routing_key
    _destination_type = destination_type

    for filter in self.methods['filter_event']:
      try:
        r = self.call_filter_event_method(filter, _event, _routing_key, _destination_type)

        if r is None:
          return None

        _event = r['event']
        _routing_key = r['routing_key']
        _destination_type = r['destination_type']

        if 'stop' in r and r['stop']:
          break

      except Exception as e:
        self.logger.error(f"Exception when calling Plugin.filter_event method of {inspect.getmodule(filter).__name__}: {e}")

    return (_event, _routing_key, _destination_type)



  def filter_webhook(self, webhook, destination_url=None):
    """call all the filter webhook methods in order and return the result or None to suppress the webhook

    Args:
        webhook (dict): the webhook to filter
        destination_url (str, optional): the URL to send the webhook to

    Returns:
        tuple: a tuple with the new webhook and destination URL, or None if suppressed
    """

    if not isinstance(webhook, dict):
      self.logger.error(f"PluginHost.filter_webhook method called with an invalid value {webhook}. Call this method with a dict.")
      return None

    _webhook = dict(webhook)
    _destination_url = destination_url

    for filter in self.methods['filter_webhook']:
      try:
        r = self.call_filter_webhook_method(filter, _webhook, _destination_url)

        if r is None:
          return None

        _webhook = r['webhook']
        _destination_url = r['destination_url']

        if r['stop']:
          break
      except Exception as e:
        self.logger.error(f"Exception when calling Plugin.filter_webhook method of {inspect.getmodule(filter).__name__}: {e}")

    return (_webhook, _destination_url)
