# Ubuntu 한 대에서 카메라와 모의 금고 실행

Ubuntu 24.04 / ROS 2 Jazzy에서 카메라 인증과 모터 노드를 함께 실행합니다. 아래 테스트에서는 모터가 시뮬레이션으로 동작합니다.

## 1. 처음 한 번 설치

저장소 최상위 폴더에서 실행합니다.

```bash
source /opt/ros/jazzy/setup.bash
python3 -m venv .venv-linux
.venv-linux/bin/python -m pip install -r txt/requirements-linux.txt
.venv-linux/bin/python -c 'import rclpy, cv2, mediapipe; print("imports OK")'
.venv-linux/bin/python py/recognition.py --self-test
(cd ros2_ws && colcon build --packages-select safe_motor_control)
```

시스템 Python과 격리된 가상환경으로 ROS 2 Jazzy의 Python 모듈과 카메라용 패키지를 사용합니다. 설치한 환경에서 한글 글꼴이 없으면 Ubuntu의 `fonts-nanum`을 설치하거나 `SAFE_FONT_PATH`에 한글 폰트 파일 경로를 지정합니다. 첫 모델 다운로드에는 인터넷이 필요합니다.

## 2. 터미널 A에서 가짜 모터 켜기

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/local_setup.bash
export ROS_DOMAIN_ID=85 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 run safe_motor_control motor_control --ros-args -p hardware:=false
```

`Simulation mode`라고 나오면 정상입니다. 기존 Windows 연동용 HTTPS 브리지와 시험용 인증 발행자는 끈 상태로 진행합니다.

## 3. 터미널 B에서 카메라를 열고 2번 칸 등록

```bash
ROS_DOMAIN_ID=85 bash sh/run_linux.sh --camera 0
```

다른 카메라를 사용할 때는 `ls -l /dev/v4l/by-id/`로 장치를 찾고 `--camera`에 해당 경로를 지정합니다.

1. 터미널에서 작업 **1**, 금고 번호 **2**, 테스트 이름, 단계 수 **1**을 순서대로 입력합니다.
2. 얼굴 창에서 얼굴을 비추고 **S**로 저장한 뒤 **Q**를 누릅니다.
3. 동작 창에서 얼굴 확인을 기다리고 손이나 팔 자세를 잡은 뒤 **P**를 누릅니다. 5초 뒤 촬영합니다.

## 4. 터미널 C에서 상태 확인하고 2번 칸 열고 닫기

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=85 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 topic echo /safe/motor_status
```

- 터미널 B의 메뉴에서 작업 **2**와 금고 번호 **2**를 선택합니다.
- 카메라 창에 얼굴이 확인되면 같은 자세를 잡고 **U**를 누릅니다. `sim:open:2`가 뜰 때까지 얼굴을 계속 비춥니다.
- 카메라 창에 초점을 두고 **C**를 누릅니다. 화면에 **가짜 모터: 2번 · 문 닫는 중 → 가짜 모터: 문 닫힘 · 대기**가 표시됩니다. 터미널 C에서는 `sim:closing:2 → sim:idle:0`이 같은 동작을 뜻합니다. C로 닫기를 시작하면 기존 인증은 끝납니다. 다시 열려면 얼굴을 확인한 후 U로 새로 인증합니다.
- **Q**를 눌러 메뉴로 돌아오고 **0**으로 프로그램을 종료합니다. 상태 터미널과 모터 터미널은 각각 **Ctrl+C**로 끝냅니다.

정상 순서는 `sim:idle:0 → sim:rotating:2 → sim:opening:2 → sim:open:2 → sim:closing:2 → sim:idle:0`입니다. 시간이 걸리거나 얼굴이 끊기면 `sim:fault:2`가 표시될 수 있으므로 모터 터미널의 오류를 확인합니다. 인증 상태는 얼굴과 패턴의 결과이고, 화면의 모터 상태 줄과 터미널 C는 문과 원판의 상태를 보여줍니다.

## 자동으로 연동 검증하기

위 수동 시험을 종료한 뒤 저장소 최상위에서 실행합니다. 이 테스트는 가짜 카메라 프레임과 제어된 얼굴·동작 인식 결과를 사용합니다. 실제 인증 흐름의 U/C 키 처리와 실제 ROS 2 토픽을 지나 별도 모의 모터 프로세스의 상태를 검증합니다.

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/local_setup.bash
ROS_DOMAIN_ID=96 .venv-linux/bin/python -B ros2_ws/tests/check_camera_to_motor.py
```

마지막 출력은 `camera-to-motor OK`입니다. 원판 차단, 인증 신호 소실, 닫힘 실패 후 재시도까지 확인하려면 [모터 단독 테스트](../ros2_ws/README.md)를 실행합니다. 실제 모터 커미셔닝은 이 절차와 별개입니다.

기술적인 토픽 계약과 변경 경위는 [기존 인수인계 기록](LINUX_ROS2_HANDOFF.md)에 보관합니다.
