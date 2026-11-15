"""Exercise the motor state machine over ROS topics with simulated encoders."""
import argparse
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from time import monotonic

import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import Bool, String

script = Path(__file__).resolve().parents[1] / 'src/safe_motor_control/scripts/motor_control'
loader = SourceFileLoader('motor_control', str(script))
spec = spec_from_loader(loader.name, loader)
module = module_from_spec(spec)
loader.exec_module(module)


class TestMotor(module.MotorControl):
    jammed = False

    def position(self, axis):
        if axis == 'door' and self.phase == 'closing' and self.jammed:
            return self.positions['door']
        return super().position(axis)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('scenario', choices=['sequence', 'retry', 'interlock', 'loss'])
    scenario = parser.parse_args().scenario
    rclpy.init(args=['--ros-args', '-p', 'move_timeout:=1.6'])
    motor = TestMotor()
    node = rclpy.create_node('motor_sequence_check')
    executor = SingleThreadedExecutor()
    executor.add_node(motor)
    executor.add_node(node)
    requests = [
        node.create_publisher(Bool, f'/safe/slot_{i}/unlock_request', 1)
        for i in (1, 2, 3)
    ]
    close = node.create_publisher(Bool, '/safe/close_request', 10)
    history = []
    status = node.create_subscription(String, '/safe/motor_status',
                                      lambda msg: history.append(msg.data), 10)

    def drive(duration, active=None, button=None):
        deadline = monotonic() + duration
        while monotonic() < deadline:
            for i, pub in enumerate(requests, 1):
                pub.publish(Bool(data=i == active))
            if button is not None:
                close.publish(Bool(data=button))
            until = monotonic() + 0.035
            while monotonic() < until:
                executor.spin_once(timeout_sec=0.008)

    try:
        if scenario == 'interlock':
            motor.positions['door'] = motor.opened
            motor.sim_targets['door'] = motor.opened
        drive(.65)
        if scenario == 'interlock':
            drive(.6, active=3)
            assert history[-1] == 'sim:door_unconfirmed:0', history
            assert not any('rotating' in s for s in history), history
        elif scenario == 'loss':
            drive(.25, active=3)
            drive(.55)
            assert 'sim:rotating:3' in history and history[-1] == 'sim:fault:3', history
            assert 'sim:opening:3' not in history, history
        else:
            drive(1.55, active=3)
            assert history[-1] == 'sim:open:3', history
            if scenario == 'retry':
                motor.jammed = True
                drive(2.0, button=True)
                assert history[-1] == 'sim:close_failed:3', history
                failed_at = len(history)
                motor.jammed = False
                drive(.65, active=2, button=True)
                drive(.22, active=2, button=False)
                assert set(history[failed_at:]) == {'sim:close_failed:3'}, history[failed_at:]
                drive(.85, active=2, button=True)
                assert 'sim:closing:3' in history[failed_at:], history
                assert history[-1] == 'sim:idle:0', history
                drive(.6)
                drive(.7, active=2, button=False)
                assert 'sim:rotating:2' in history, history
            else:
                drive(.85, button=True)
                sequence = ['sim:checking_door:0', 'sim:idle:0', 'sim:rotating:3',
                            'sim:opening:3', 'sim:open:3', 'sim:closing:3', 'sim:idle:0']
                seen = [s for i, s in enumerate(history) if not i or s != history[i-1]]
                assert seen == sequence or seen == sequence[1:], seen
        print(scenario, 'OK', list(dict.fromkeys(history)), flush=True)
    finally:
        executor.shutdown()
        node.destroy_node()
        motor.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
