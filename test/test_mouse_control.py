import unittest

from src.mouse_control import DrawPoint, map_path_to_target

class MouseControlTest(unittest.TestCase):
    def test_map_path_to_target_fits_inside_margined_window(self):
        path = [{"x": 0, "y": 0}, {"x": 100, "y": 50}]
        target = {"x": 10, "y": 20, "width": 300, "height": 300}
        mapped = map_path_to_target(path, (100, 50), target)
        self.assertEqual(mapped, [DrawPoint(10, 95), DrawPoint(310, 245)])

if __name__ == "__main__":
    unittest.main()
