"""Local ROS 2 output. No images, names or biometric descriptors are published."""
import threading
import time


def authorization_values(slot, allowed, updated, now, ttl=0.4):
    """Expire authentication when camera processing stops making progress."""
    fresh = allowed and 0 <= now - updated < ttl
    return [bool(fresh and slot == number) for number in (1, 2, 3)]


class Ros2AuthOutput:
    def __init__(self):
        import rclpy
        from rclpy.executors import SingleThreadedExecutor
        from std_msgs.msg import Bool, String
        self.rclpy, self.Bool = rclpy, Bool
        self.context = rclpy.context.Context()
        rclpy.init(args=[], context=self.context)
        self.node = rclpy.create_node('safe_camera_auth', context=self.context)
        self.publishers = [self.node.create_publisher(
            Bool, f'/safe/slot_{i}/unlock_request', 1) for i in (1, 2, 3)]
        self.close_publisher = self.node.create_publisher(Bool, '/safe/close_request', 1)
        self.lock = threading.Lock()
        self.snapshot = (None, False, 0.)
        self.close_until = 0.
        self.motor_status = None
        self.status_subscription = self.node.create_subscription(
            String, '/safe/motor_status', self._on_motor_status, 1)
        self.executor = SingleThreadedExecutor(context=self.context)
        self.executor.add_node(self.node)
        self.error = None
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def update(self, slot, allowed):
        if self.error:
            raise RuntimeError('ROS 2 output stopped') from self.error
        with self.lock:
            self.snapshot = (slot, bool(allowed), time.monotonic())

    def request_close(self):
        with self.lock:
            now = time.monotonic()
            if self.motor_status is None or now - self.motor_status[1] > 1.0:
                return False
            _, _, tail = self.motor_status[0].partition(':')
            phase, _, _ = tail.partition(':')
            if phase not in ('open', 'door_unconfirmed', 'close_failed'):
                return False
            self.snapshot = (None, False, 0.)
            self.close_until = now + 0.3
            return True

    def _on_motor_status(self, message):
        with self.lock:
            self.motor_status = (message.data, time.monotonic())

    def motor_status_line(self):
        with self.lock:
            latest = self.motor_status
        if latest is None or time.monotonic() - latest[1] > 1.0:
            return '모터 상태: 신호 대기 중'
        mode, _, tail = latest[0].partition(':')
        phase, _, slot = tail.partition(':')
        labels = {
            'checking_door': '문 닫힘 확인 중',
            'door_unconfirmed': '문 닫힘 미확인 · C로 닫기',
            'idle': '문 닫힘 · 대기',
            'rotating': '원판 정렬 중',
            'opening': '문 여는 중',
            'open': '문 열림',
            'closing': '문 닫는 중',
            'close_failed': '닫힘 실패 · 통로 확인 후 C로 재시도',
            'fault': '오류 · 모터 터미널 확인',
        }
        if mode not in ('sim', 'hardware') or phase not in labels:
            return '모터 상태: 알 수 없는 신호'
        prefix = '가짜 모터' if mode == 'sim' else '모터'
        selected = f'{slot}번 · ' if slot in ('1', '2', '3') else ''
        return f'{prefix}: {selected}{labels[phase]}'

    def _publish(self, values, close=False):
        for publisher, value in zip(self.publishers, values):
            publisher.publish(self.Bool(data=value))
        self.close_publisher.publish(self.Bool(data=close))

    def _run(self):
        try:
            while not self.stopped.is_set():
                with self.lock:
                    now = time.monotonic()
                    values = authorization_values(*self.snapshot, now)
                    close = now < self.close_until
                self._publish(values, close)
                self.executor.spin_once(timeout_sec=0)
                self.stopped.wait(0.1)
        except Exception as error:
            self.error = error

    def close(self):
        self.stopped.set()
        self.thread.join()
        try:
            self._publish([False, False, False])
        finally:
            self.executor.shutdown()
            self.node.destroy_node()
            self.rclpy.shutdown(context=self.context)
