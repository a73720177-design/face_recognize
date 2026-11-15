# 프로젝트 폴더 구성

Ubuntu에서 카메라 인증과 모터 제어를 함께 실행하는 소스입니다. 개발 PC의 현재 로컬 체크아웃은 `work/linux-main/`이며, **그 폴더 안의 구조가 GitHub 저장소에 대응**합니다.

| 폴더 | 내용 |
| --- | --- |
| `py/` | 얼굴·손 동작 인증 소스, Python 단위 테스트, [2번 칸 시험 도구](../py/open_slot2_for_test.py) |
| `sh/` | [Ubuntu 카메라 실행](../sh/run_linux.sh), [모터 실행·조회](../sh/run_safe_motors.sh), [카메라 모의 연동](../sh/live-camera-session.sh) |
| `txt/` | Python 설치 목록. Ubuntu는 `requirements-linux.txt` 사용 |
| `md/` | 현재 안내. `archive/`는 과거 실습 자료 |
| `ps1/` | Windows 개발 환경 실행 도구 |
| `ros2_ws/` | ROS 2 모터 패키지, YAML 설정, 토픽 연동 테스트 |

개발 PC에서는 체크아웃 밖의 이전 코드·배포본·원본 검증 로그를 별도로 보관합니다. 카메라 등록 데이터, 인증 키, 모델 캐시, 가상환경, 빌드 결과물과 실행 로그는 각 PC에서 관리합니다.

현재 사용 절차는 [Ubuntu 2번 칸 시험 안내](LINUX_ROS2_GUIDE.md)에서 시작합니다.
