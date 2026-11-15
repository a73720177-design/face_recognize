import unittest
from ros2_auth import authorization_values


class AuthorizationTests(unittest.TestCase):
    def test_only_selected_slot(self):
        self.assertEqual(authorization_values(2, True, 10., 10.1), [False, True, False])

    def test_expired_frame_revokes_all(self):
        self.assertEqual(authorization_values(2, True, 10., 10.4), [False]*3)

    def test_denied_and_invalid_slot(self):
        self.assertEqual(authorization_values(2, False, 10., 10.1), [False]*3)
        self.assertEqual(authorization_values(4, True, 10., 10.1), [False]*3)

    def test_clock_reversal(self):
        self.assertEqual(authorization_values(1, True, 10., 9.), [False]*3)
