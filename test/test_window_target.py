import unittest

from src.window_target import TargetWindow, activate_window, full_screen_target

class WindowTargetTest(unittest.TestCase):
    def test_label_includes_title_size_and_origin(self):
        window = TargetWindow("Paint", 10, 20, 640, 480)
        self.assertEqual(window.label, "Paint — 640×480 at 10,20")

    def test_full_screen_target_uses_screen_size(self):
        window = full_screen_target(1920, 1080)
        self.assertEqual((window.title, window.x, window.y, window.width, window.height), ("Full screen", 0, 0, 1920, 1080))

    def test_full_screen_target_does_not_require_activation(self):
        ok, message = activate_window(full_screen_target(1920, 1080))
        self.assertTrue(ok)
        self.assertIn("No external window activation", message)

if __name__ == "__main__":
    unittest.main()
