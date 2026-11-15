# Linux 단일 환경 구동 — Linux GPT 인수인계

> 최초 인수인계 당시의 기록입니다. 현재 설치 및 실행 절차는 [Linux 실행 및 검증 안내](LINUX_ROS2_GUIDE.md)를 사용하세요.

결정일: 2026-11-15

## 사용자가 확정한 결정

- ROS 2 사용 경험이 프로젝트의 목적이므로 ROS 2를 유지합니다. 기존 모터 제어 코드도 사용자가 구현한 작업입니다.
- 현재 노트북은 Windows/Linux 듀얼부팅입니다. 두 OS를 동시에 실행한다고 가정하지 않습니다.
- 실제 금고는 Linux 한 대에서 카메라 인증과 ROS 2 모터 제어를 모두 실행합니다. Windows는 필수가 아닙니다.
- 노트북 내장 카메라 대신 금고 상단에 설치할 카메라를 사용합니다.
- Windows–Linux HTTPS 브리지, IP, 인증서, 토큰은 이 구성에 필요 없습니다. Linux의 기존 작업 파일은 확인 없이 삭제하지 않습니다.

```text
금고 상단 카메라
  → recognition.py / safe_app.py: 얼굴 → 손·팔 자세 순서 인증
  → ros2_auth.py: safe_camera_auth 노드
  → /safe/slot_1~3/unlock_request
  → safe_motor_control: 원판 정렬 → 문 열기 → 닫기 요청 → 문 닫기
```

금고는 3칸, 한 사용자당 한 칸, 한 칸당 한 소유자입니다. 등록은 단계마다 P를 누르고 5초 뒤 촬영합니다. 표정 인증은 사용하지 않습니다. 기존 모터 노드의 원판 1개와 공용 문 구조를 기준으로 합니다.

## 이번에 추가한 코드와 계약

- `py/recognition.py --ros2`: 로컬 ROS 2 출력을 활성화합니다. 생략하면 모터 토픽을 발행하지 않습니다. 영상 파일·headless·자체 점검·단독 얼굴 등록과 함께 쓰는 것은 차단합니다.
- `--camera`: 숫자 인덱스 또는 `/dev/v4l/by-id/...` 경로를 받습니다.
- `py/vision_utils.py`: Linux Nanum/Noto 한글 폰트를 지원합니다. `SAFE_FONT_PATH`로 실제 폰트 경로를 지정할 수도 있습니다.
- `py/ros2_auth.py`: `std_msgs/msg/Bool`로 아래 세 토픽 모두 약 10Hz 발행합니다. 이름·영상·생체 특징은 보내지 않습니다.

```text
/safe/slot_1/unlock_request
/safe/slot_2/unlock_request
/safe/slot_3/unlock_request
```

처음에는 모두 false입니다. 잠금 해제 모드에서 현재 소유자의 얼굴이 현재 프레임에 있고 패턴 인증까지 완료된 경우에만 선택한 칸이 true입니다. 등록 모드에서는 항상 모두 false입니다. 기존 모터 노드는 idle에서 세 false를 받은 후 한 칸의 true를 받아야 출발합니다.

카메라 처리 갱신이 0.4초 이상 없으면 발행 스레드는 모두 false로 바꿉니다. 프로세스 전체가 멈추면 모터 노드의 0.5초 신선도 검사로 감지합니다. 실제 추론 성능에 따라 이 시간과 안전 동작을 Linux에서 함께 검증해야 합니다. rotating/opening 중 인증이 없어지면 기존 모터 노드는 fault가 됩니다. 이동이 끝날 때까지 얼굴을 유지해야 합니다.

인증 화면의 C는 `/safe/close_request`에 약 0.3초 true 후 false를 보냅니다. 모터는 상승 에지로 닫습니다. 재시도는 이전 펄스가 끝난 뒤 C를 다시 누릅니다. 닫기는 등록 화면에서도 요청할 수 있습니다. 카메라 세션 종료 시 false를 발행하고 노드를 종료합니다. 다음 세션에서 다시 생성합니다.

`/safe/motor_status`는 기존 모터 노드가 발행합니다. 현재 인증 UI는 이 상태를 구독하지 않으므로 **인증 성공 표시가 실제 문 열림 확인은 아닙니다.**

## Linux GPT가 진행할 절차

1. 먼저 Linux 작업 폴더의 Git 상태와 미반영 파일을 백업합니다. Linux에 있는 `work/ros2_split_ws`, 실행 스크립트와 브리지 작업을 무조건 덮어쓰지 않습니다. 이 저장소의 모터 코드는 `ros2_ws/src/safe_motor_control`입니다. 기존 모터와 저장소 모터 중 하나만 실행합니다.
2. 최신 main을 받고 기존 모터 노드의 토픽·상태 전이와 위 계약을 비교합니다. 기존 HTTPS 브리지가 같은 토픽을 발행한다면 끕니다. 인증 발행자는 하나만 사용합니다.
3. Ubuntu 24.04 / ROS 2 Jazzy의 시스템 Python 3.12와 rclpy를 사용합니다. Windows 가상환경을 복사하지 않습니다.

저장소 최상위에서:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install python3-venv fonts-nanum
python3 -m venv --system-site-packages .venv-linux
.venv-linux/bin/python -m pip install -r txt/requirements.txt
.venv-linux/bin/python -c 'import rclpy, cv2, mediapipe; print("imports OK")'
.venv-linux/bin/python -m unittest discover -s py -p 'test_*.py'
.venv-linux/bin/python py/recognition.py --self-test
```

`--system-site-packages`는 apt의 ROS Python 패키지를 가상환경에서도 찾기 위해 사용합니다. requirements의 고정 버전은 Windows에서 쓰던 값이며 Linux wheel 설치는 이번에 검증하지 않았습니다. 설치 실패 시 Linux 호환 버전을 확인하여 별도 변경하고 결과를 기록합니다. UI가 필요하므로 headless OpenCV로 대체하지 않습니다.

4. `ls -l /dev/v4l/by-id/`로 금고 카메라를 찾습니다. 가능하면 인덱스 대신 고정 장치 경로를 사용합니다. 그래픽 데스크톱에서 실행합니다.
5. 실제 모터 없이 아래처럼 두 노드를 연결해 검증합니다.

터미널 A — 시뮬레이션:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=85
cd ros2_ws
colcon build --packages-select safe_motor_control
source install/local_setup.bash
ros2 run safe_motor_control motor_control
```

터미널 B — 저장소 최상위에서 인증:

```bash
bash sh/run_linux.sh --camera 0
# 또는 --camera /dev/v4l/by-id/실제장치-video-index0
```

터미널 C — 모터 상태 확인:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=85
ros2 topic echo /safe/motor_status
```

사용자·패턴 등록 후 잠금 해제 메뉴에서 U로 인증합니다. 시뮬레이션 정렬·열림을 확인하고 C로 닫습니다. 모든 노드의 ROS_DOMAIN_ID는 같아야 합니다. 기존 시나리오 테스트는 인증 노드와 다른 시간에 실행하여 발행자가 겹치지 않게 합니다. [기존 ROS 2 시험 안내](../ros2_ws/README.md)를 참고하세요.

## 미검증과 후속 작업

- 이번 변경은 Windows 코드 검사·단위 테스트만 수행했습니다. Linux 설치, 실제 rclpy 통신, USB 카메라와 실제 모터 구동은 검증하지 않았습니다. 이전 PR의 모터 시험 기록과 구분합니다.
- Linux GPT는 실제 카메라 인증 → 토픽 → 시뮬레이션 전체 연결을 먼저 검증합니다. 느린 추론·카메라 끊김·얼굴 상실·메뉴 복귀·L 잠금·등록 모드에서 false/fault 동작을 확인하고 결과를 기록합니다.
- 문을 닫은 후 인증 true가 남아 있어도 모터는 세 false를 받기 전에는 다시 열지 않습니다. L로 잠근 뒤 얼굴과 패턴을 다시 인증하는 절차를 확인합니다.
- R은 소유자·패턴 초기화이며 실제 문 닫기가 아닙니다. 먼저 C로 닫고 모터 상태를 확인합니다. 모터 상태 UI 표시와 문 열린 동안 소유권 초기화 차단은 후속 작업입니다.
- fault는 원인을 확인하고 모터 노드를 재시작합니다. 실제 하드웨어 위치와 기구 간섭은 현장에서 보정합니다.
- ROS 토픽 자체는 인증 권한을 검증하지 않으므로 신뢰하는 로컬 실행 환경을 전제로 합니다. 생체 확인, 얼굴과 손의 동일 인물 연결, 데이터 암호화와 실제 문 센서는 구현 완료로 표시하지 않습니다.

Linux GPT에게 전달할 요청: “이 문서를 기준으로 Linux 단일 환경의 인증 노드를 기존 ROS 2 모터 노드에 연결해 주세요. Linux에만 있는 코드를 보존하고, 카메라와 시뮬레이션 전체 연결 및 인증 소실 처리를 먼저 검증한 뒤 실제 하드웨어 단계로 진행해 주세요.”
