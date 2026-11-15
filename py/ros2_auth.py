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
        from std_msgs.msg import Bool
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
            self.close_until = time.monotonic() + 0.3

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
                self.stopped.wait(0.1)
        except Exception as error:
            self.error = error

    def close(self):
        self.stopped.set()
        self.thread.join()
        try:
            self._publish([False, False, False])
        finally:
            self.node.destroy_node()
            self.rclpy.shutdown(context=self.context)
