import unittest

from dataclasses import dataclass

from src.autodraw_engine import analyze_colors, build_layer_path, drawing_area_from_target, fit_to_area, nearest_neighbor_path, threshold_sketch_pixels, serialize_project

class AutoDrawEngineTest(unittest.TestCase):
    def test_analyze_colors_groups_and_sorts_darkest_first(self):
        layers = analyze_colors([(1, 1, 1), (2, 2, 2), (250, 250, 250)], tolerance=16)
        self.assertEqual(len(layers), 2)
        self.assertEqual(layers[0].color, (0, 0, 0))
        self.assertEqual(layers[0].count, 2)

    def test_fit_to_area_preserves_aspect_ratio(self):
        fit = fit_to_area((320, 260), (250, 200))
        self.assertEqual(fit["height"], 200)
        self.assertEqual(fit["width"], 246.15)

    def test_nearest_neighbor_path_visits_nearest_point(self):
        path = nearest_neighbor_path([{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 1, "y": 0}])
        self.assertEqual([point["x"] for point in path], [0, 1, 10])

    def test_threshold_sketch_pixels_keeps_dark_marks(self):
        points = threshold_sketch_pixels([(10, 10, 10), (240, 240, 240)], (2, 1), threshold=190)
        self.assertEqual(points, [{"x": 0, "y": 0}])


    def test_brush_size_controls_layer_path_step(self):
        pixels = [(0, 0, 0)] * 16
        path = build_layer_path(pixels, (4, 4), (0, 0, 0), tolerance=1, sample_step=1, brush_size=2)
        self.assertEqual(len(path), 4)

    def test_drawing_area_from_target_applies_margin_and_end_points(self):
        @dataclass(frozen=True)
        class Target:
            x: int = 10
            y: int = 20
            width: int = 100
            height: int = 50

        area = drawing_area_from_target(Target(), margin=5)
        self.assertEqual(area, {"x": 15, "y": 25, "width": 90, "height": 40, "end_x": 105, "end_y": 65})

    def test_serialize_project_contains_layers_and_keybinds(self):
        layers = analyze_colors([(10, 10, 10)], tolerance=16)
        project = serialize_project(layers, "Scale to 10 x 10", progress=0, brush_size=7, target_area={"x": 5})
        self.assertEqual(project["version"], 1)
        self.assertEqual(project["layers"][0]["count"], 1)
        self.assertEqual(project["brush_size"], 7)
        self.assertEqual(project["target_area"], {"x": 5})
        self.assertIn("emergency_stop", project["keybinds"])

if __name__ == "__main__":
    unittest.main()
