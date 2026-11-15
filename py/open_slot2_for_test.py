"""Send a single slot-2 commissioning request on an isolated ROS domain."""
import argparse
from time import monotonic

import rclpy
from std_msgs.msg import Bool, String


def request_open(node, mode):
    pubs = [
        node.create_publisher(Bool, f'/safe/slot_{number}/unlock_request', 1)
        for number in (1, 2, 3)
    ]
    state = None

    def receive(message):
        nonlocal state
        state = message.data

    node.create_subscription(String, '/safe/motor_status', receive, 10)

    def send(active):
        for number, publisher in enumerate(pubs, 1):
            publisher.publish(Bool(data=active and number == 2))
        rclpy.spin_once(node, timeout_sec=0.1)

    def wait_for_ready():
        ready_since = None
        deadline = monotonic() + 8
        while monotonic() < deadline:
            send(False)
            if state == f'{mode}:idle:0' and all(pub.get_subscription_count() == 1 for pub in pubs):
                ready_since = ready_since or monotonic()
                if monotonic() - ready_since > 0.6:
                    return True
            else:
                ready_since = None
        return False

    if not wait_for_ready():
        print(f'대기 상태를 확인하지 못했습니다. 마지막 상태: {state}')
        return 1
    if input('금고 주변을 확인한 뒤 2번 칸을 열려면 OPEN을 입력하세요: ').strip() != 'OPEN':
        print('열기 취소')
        return 1
    if not wait_for_ready():
        print(f'열기 취소. 마지막 상태: {state}')
        return 1

    deadline = monotonic() + 35
    last_reported = None
    while monotonic() < deadline:
        send(True)
        if state != last_reported:
            print(state, flush=True)
            last_reported = state
        if state == f'{mode}:open:2':
            send(False)
            return 0
        if state and (':fault:' in state or ':door_unconfirmed:' in state):
            send(False)
            return 1
    send(False)
    print('시간 안에 열림 상태를 받지 못했습니다.')
    return 1


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--sim', action='store_true', help='Use the simulated motor node (default)')
    modes.add_argument('--hardware', action='store_true', help='Use commissioned hardware')
    args = parser.parse_args()
    rclpy.init(args=[])
    node = rclpy.create_node('slot2_commissioning_test')
    try:
        return request_open(node, 'hardware' if args.hardware else 'sim')
    except (KeyboardInterrupt, EOFError):
        return 1
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
