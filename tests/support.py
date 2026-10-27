import importlib
import unittest


class SamovarTestCase(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module("flying_samovar")

    def make_samovar(self, **kwargs):
        values = dict(name="Пых", wing_span_m=2.5, max_speed_kmh=40)
        values.update(kwargs)
        return self.module.FlyingSamovar(**values)

    def state(self, samovar):
        return {name: getattr(samovar, name) for name in (
            "name", "wing_span_m", "max_speed_kmh", "steam", "position_km",
            "wings_deployed", "is_flying",
        )}

    def assert_unchanged_error(self, samovar, error, action):
        before = self.state(samovar)
        with self.assertRaises(error):
            action()
        self.assertEqual(self.state(samovar), before)

    def assert_result(self, actual, expected):
        self.assertIs(type(actual), float)
        self.assertAlmostEqual(actual, expected, places=7)

    def assert_calculated_state(self, actual, expected, changed):
        """Вычисленные поля — с погрешностью, остальные — точно."""
        self.assertEqual(actual.keys(), expected.keys())
        for name, value in expected.items():
            with self.subTest(attribute=name):
                if name in changed:
                    self.assert_result(actual[name], value)
                else:
                    self.assertIs(type(actual[name]), type(value))
                    self.assertEqual(actual[name], value)
