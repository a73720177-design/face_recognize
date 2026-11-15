# ROS 2 모터 시뮬레이션

Ubuntu 24.04와 ROS 2 Jazzy에서 금고의 원판 모터와 문 모터를 가상 엔코더로 시험합니다. Windows 인증, 웹캠, U2D2 및 DYNAMIXEL SDK 없이 실행할 수 있습니다. 시뮬레이션이 기본 모드입니다.

## 먼저 빌드하기

저장소 최상위 폴더에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --packages-select safe_motor_control
source install/local_setup.bash
```

빌드가 끝나면 `1 package finished`가 출력됩니다.

## 동작 검증

이 테스트는 모터 노드와 시험 신호 발행자를 함께 실행합니다. 별도로 모터 노드를 실행할 필요가 없습니다. 아래에서는 일반 작업과 겹치지 않도록 로컬 ROS 도메인 85를 사용합니다.

```bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=85
python3 -B tests/check_motor_sequence.py sequence
python3 -B tests/check_motor_sequence.py retry
python3 -B tests/check_motor_sequence.py interlock
python3 -B tests/check_motor_sequence.py loss
```

| 시험 | 확인하는 동작 | 정상 출력 |
| --- | --- | --- |
| `sequence` | 칸 정렬 → 문 열기 → 닫기 → 대기 | `sequence OK` |
| `retry` | 가짜 문 걸림 후 원판 차단. 닫기 버튼을 계속 눌러도 재구동하지 않고, 버튼을 뗐다 다시 누르면 닫기 재시도 | `retry OK` |
| `interlock` | 문 엔코더 값이 닫힘 범위 밖이면 원판 회전 차단 | `interlock OK` |
| `loss` | 원판이 회전하는 동안 인증 상태가 사라지면 오류 전환 | `loss OK` |

`retry`와 `loss` 중에는 각 오류 상황을 재현하므로 경고나 오류 로그가 먼저 표시될 수 있습니다. 해당 시험의 마지막 `OK`가 통과를 뜻합니다.

## 시뮬레이션 노드만 실행

위의 자동 검증 대신 노드에 직접 연결하려면, 빌드 후 같은 터미널에서 다음을 실행합니다.

```bash
ros2 run safe_motor_control motor_control
```

`Simulation mode`가 보이면 정상입니다. 노드는 `/safe/motor_status`에 `sim:idle:0` 같은 상태를 발행하고, 종료할 때는 Ctrl+C를 누릅니다.

실제 모터와 기구 구동은 이 검증의 범위 밖입니다. 동봉된 하드웨어 설정의 위치값은 현장 보정이 필요한 상태입니다.
