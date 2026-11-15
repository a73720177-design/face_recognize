# 얼굴·동작 인증 금고

[프로젝트 설명과 실행 방법](../md/README.md)

실제 금고는 Linux 한 대에서 카메라 인증과 ROS 2 모터 제어를 함께 실행합니다. [Linux 구동 결정 및 GPT 인수인계](../md/LINUX_ROS2_HANDOFF.md)를 먼저 확인하세요.

- `py/`: Python 코드와 테스트
- `md/`: 프로젝트 문서
- `txt/`: 라이브러리 설치 목록
- `ps1/`: PowerShell 실행 스크립트
- `ros2_ws/`: ROS 2 패키지와 시뮬레이션 테스트

```powershell
.\.venv\Scripts\python.exe py/recognition.py
```

[ROS 2 실행 안내](../ros2_ws/README.md)
