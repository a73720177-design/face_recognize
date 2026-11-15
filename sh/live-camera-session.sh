#!/usr/bin/env bash
set -eo pipefail
umask 077
case "${1:-}" in
    ""|retest) ;;
    -h|--help)
        printf '%s\n' '사용법: bash sh/live-camera-session.sh [retest]' \
            '인자 없이 실행하면 등록 메뉴를 엽니다. retest는 등록된 2번 칸을 바로 인증합니다.'
        exit 0 ;;
    *)
        printf '알 수 없는 인자: %s\n' "$1" >&2
        exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
    printf '%s\n' '사용법: bash sh/live-camera-session.sh [retest]' >&2
    exit 2
fi
base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$base"
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/local_setup.bash
runs="${SAFE_VERIFICATION_LOG_DIR:-$base/verification/logs/runs}"
mkdir -p "$runs"
output="$(mktemp -d "$runs/session-XXXXXXXX")"
printf '검증 로그: %s\n' "$output"
export ROS_DOMAIN_ID=94 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST PYTHONUNBUFFERED=1
if [[ "${1:-}" == "retest" ]]; then
    export ROS_DOMAIN_ID=95
    set -- --safe-mode verify --safe-number 2
else
    set --
fi
"$(ros2 pkg prefix safe_motor_control)/lib/safe_motor_control/motor_control" --ros-args -p hardware:=false > "$output/live_motor.log" 2>&1 &
motor_pid=$!
ros2 topic echo /safe/motor_status std_msgs/msg/String > "$output/live_status.log" 2>&1 &
status_pid=$!
trap 'kill -TERM "$status_pid" "$motor_pid" 2>/dev/null || true' EXIT
if [[ $# == 0 ]]; then
    printf '%s\n' '가짜 모터 시험: 등록 1 → 금고 번호 2 → 테스트 이름 → 동작 1단계' '얼굴 창에서 S, Q → 동작 창에서 자세를 유지하고 P → 등록 후 메뉴 2, 금고 번호 2'
fi
printf '%s\n' '같은 자세로 U → 문 열림 확인 → C로 닫기 → 문 닫힘 확인 → Q'
timeout --foreground 300s bash sh/run_linux.sh --camera 0 "$@"
