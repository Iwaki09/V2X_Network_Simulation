#!/bin/bash

# SUMO実行スクリプト
# Usage:
#   ./run_sumo.sh          # GUIなしで実行
#   ./run_sumo.sh gui      # GUI付きで実行

SUMO_CONFIG="sumo_scenarios/config.sumocfg"

if [ "$1" == "gui" ]; then
    echo "Starting SUMO with GUI..."
    sumo-gui -c $SUMO_CONFIG
else
    echo "Starting SUMO (headless mode)..."
    sumo -c $SUMO_CONFIG
fi
