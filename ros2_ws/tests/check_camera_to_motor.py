"""Run the real authorization/key path against simulated motors and controlled inputs."""
import os
from pathlib import Path
import signal
from subprocess import Popen
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import rclpy
from ament_index_python.packages import get_package_prefix
from std_msgs.msg import Bool, String

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'py'))
from safe_app import run_safe
from safe_slot import SafeSlotStore

POSE = {'handRight': [[0, 0], [0, 1]]}
USER = 'integration-test'


class Camera:
    def isOpened(self):
        return True

    def read(self):
        sleep(0.05)
        return True, np.zeros((240, 320, 3), dtype=np.uint8)

    def release(self):
        pass


class Inputs:
    database = {USER: []}
    visible = True

    def identify_person(self, _frame):
        return '', None, USER if self.visible else None


def main():
    os.environ.setdefault('ROS_DOMAIN_ID', '96')
    os.environ['ROS_AUTOMATIC_DISCOVERY_RANGE'] = 'LOCALHOST'
    executable = Path(get_package_prefix('safe_motor_control')) / 'lib/safe_motor_control/motor_control'
    with Popen([str(executable), '--ros-args', '-p', 'hardware:=false']) as motor:
        try:
            return exercise()
        finally:
            motor.send_signal(signal.SIGINT)
            motor.wait(timeout=5)


def exercise():
    rclpy.init()
    monitor = rclpy.create_node('camera_to_motor_check')
    states, close_values, slot2_values = [], [], []
    displayed = set()
    monitor.create_subscription(String, '/safe/motor_status', lambda msg: states.append(msg.data), 10)
    monitor.create_subscription(Bool, '/safe/close_request', lambda msg: close_values.append(msg.data), 10)
    monitor.create_subscription(Bool, '/safe/slot_2/unlock_request', lambda msg: slot2_values.append(msg.data), 10)

    with TemporaryDirectory() as directory:
        root = Path(directory)
        slot = SafeSlotStore(root / 'data' / 'safe_slot.json', 2)
        slot.load_for(USER)
        slot.save(USER, [{'pose': POSE, 'preview': ''}])
        inputs = Inputs()
        start = monotonic()
        pressed_open = pressed_close = False
        close_started_at = None
        slot2_close_start = None

        def key(_delay):
            nonlocal pressed_open, pressed_close, close_started_at, slot2_close_start
            for _ in range(12):
                rclpy.spin_once(monitor, timeout_sec=0)
            if monotonic() - start > 18:
                raise AssertionError(f'No complete flow: {list(dict.fromkeys(states))}')
            if not pressed_open and monotonic() - start > 1.4 and 'sim:idle:0' in states:
                pressed_open = True
                return ord('U')
            if not pressed_close and '가짜 모터: 2번 · 문 열림' in displayed:
                pressed_close = True
                close_started_at = monotonic()
                slot2_close_start = len(slot2_values)
                displayed.discard('가짜 모터: 문 닫힘 · 대기')
                return ord('C')
            if (pressed_close and 'sim:closing:2' in states and states[-1] == 'sim:idle:0'
                    and monotonic() - close_started_at > 1.6):
                close_pulse_ended = True in close_values and False in close_values[
                    close_values.index(True) + 1:
                ]
                after_close = slot2_values[slot2_close_start + 2:]
                if not after_close or any(after_close):
                    raise AssertionError('Authorization returned after closing without another U press')
                if close_pulse_ended and '가짜 모터: 문 닫힘 · 대기' in displayed:
                    return ord('Q')
            return -1

        def record_panel(_frame, lines, **_options):
            displayed.update(text for text, *_ in lines)

        detector = SimpleNamespace(detect_for_video=lambda *_: SimpleNamespace(
            pose_landmarks=[], hand_landmarks=[], handedness=[]))
        args = SimpleNamespace(video=None, headless=False, safe_mode='verify',
            safe_number=2, expected_user=None, face_threshold=0.45, pattern_tolerance=0.23,
            ros2=True, camera=0, no_mirror=True, max_frames=0)
        try:
            with patch('safe_app.ROOT', root), patch('safe_app.FaceIdentity', return_value=inputs), \
                 patch('safe_app.create_detectors', return_value=(detector, detector)), \
                 patch('safe_app.download_models', return_value={}), \
                 patch('safe_app.describe_pose', return_value=POSE), \
                 patch('safe_app.wrap_panel_lines', side_effect=lambda lines, width: lines), \
                 patch('safe_app.draw_korean_text', side_effect=record_panel), patch('safe_app.cv2.VideoCapture', return_value=Camera()), \
                 patch('safe_app.cv2.namedWindow'), patch('safe_app.cv2.setWindowTitle'), \
                 patch('safe_app.cv2.imshow'), patch('safe_app.cv2.getWindowProperty', return_value=1), \
                 patch('safe_app.cv2.destroyAllWindows'), patch('safe_app.cv2.waitKey', side_effect=key):
                run_safe(args)
            ordered = ['sim:idle:0', 'sim:rotating:2', 'sim:opening:2',
                       'sim:open:2', 'sim:closing:2', 'sim:idle:0']
            distinct = [value for i, value in enumerate(states) if not i or states[i-1] != value]
            if distinct and distinct[0] == 'sim:checking_door:0':
                distinct = distinct[1:]
            if distinct != ordered or True not in slot2_values or True not in close_values:
                raise AssertionError((distinct, slot2_values, close_values))
            print(' → '.join(ordered))
            print('camera-to-motor OK (controlled camera and key inputs; real ROS 2 topics)')
            return 0
        finally:
            monitor.destroy_node()
            rclpy.try_shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
