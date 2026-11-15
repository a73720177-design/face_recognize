#!/usr/bin/env bash
set -eo pipefail
base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$base/ros2_ws/install/local_setup.bash"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${SAFE_ROS_DISCOVERY_RANGE:-LOCALHOST}"
prefix="$(ros2 pkg prefix safe_motor_control)"
exec "${SAFE_MOTOR_PYTHON:-python3}" "$prefix/lib/safe_motor_control/motor_control" "$@"
