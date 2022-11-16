#!/bin/sh

# if the plugins dir is empty, create the lib dir and put in some sample plugins
BASE_PATH=$(python3 -c 'import pdaltagent; print(pdaltagent.__path__[0])')
PLUGIN_PATH="${BASE_PATH}/plugins"
SCRIPT_PATH="${BASE_PATH}/scripts"
if [ -d ${PLUGIN_PATH} ] && [ ! "$(ls -A ${PLUGIN_PATH})" ]; then
  mkdir ${PLUGIN_PATH}/lib
  cp ${SCRIPT_PATH}/default_plugin.py ${PLUGIN_PATH}/
  cp ${SCRIPT_PATH}/example_filter_plugin.py ${PLUGIN_PATH}/
  cp ${SCRIPT_PATH}/example_fetch_plugin.py ${PLUGIN_PATH}/
fi

# don't leave auth info sitting around
rm -rf /root/.config/pagerduty-cli

# if API token is set, then configure PD CLI with the new token
if [ ${PDAGENTD_API_TOKEN:-no} != 'no' ]; then
  pd auth add -t ${PDAGENTD_API_TOKEN} 2>&1
fi
