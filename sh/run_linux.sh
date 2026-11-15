#!/usr/bin/env bash
set -eo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
set -u
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-85}"
exec "$task_root/.venv-linux/bin/python" "$task_root/py/recognition.py" --ros2 "$@"
