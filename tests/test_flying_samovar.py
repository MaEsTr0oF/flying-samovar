from tests.support import SamovarTestCase


class FlyingSamovarTests(SamovarTestCase):
    def test_TC_M_01_defaults_and_errors(self):
        """TC_M_01: начальное состояние и иерархия исключений."""
        # Arrange
        expected = dict(name=" Пых ", wing_span_m=2.5, max_speed_kmh=40.0,
                        steam=100.0, position_km=0.0,
                        wings_deployed=False, is_flying=False)
        # Act
        samovar = self.make_samovar(name=" Пых ")
        # Assert
        self.assertEqual(self.state(samovar), expected)
        for name in ("wing_span_m", "max_speed_kmh", "steam", "position_km"):
            self.assertIs(type(getattr(samovar, name)), float)
        self.assertIs(type(samovar.name), str)
        self.assertIs(type(samovar.wings_deployed), bool)
        self.assertIs(type(samovar.is_flying), bool)
        self.assertEqual(self.module.SamovarError.__bases__, (Exception,))
        for name in ("SamovarWingsFolded", "SamovarNotEnoughSteam",
                     "SamovarCannotMoveHere", "SamovarInFlight"):
            self.assertEqual(getattr(self.module, name).__bases__,
                             (self.module.SamovarError,))

    def test_TC_M_02_constructor_boundaries(self):
        """TC_M_02: допустимые границы параметров конструктора."""
        for wing, speed, steam in [(1, 1, 0), (10, 120, 100), (2.5, 40.5, 0.25)]:
            with self.subTest(wing=wing, speed=speed, steam=steam):
                # Arrange
                values = dict(wing_span_m=wing, max_speed_kmh=speed, steam=steam)
                # Act
                samovar = self.make_samovar(**values)
                # Assert
                for name, value in values.items():
                    self.assert_result(getattr(samovar, name), float(value))

    def test_TC_M_03_invalid_name(self):
        """TC_M_03: пустое имя и неверный тип имени."""
        for value, error in [("", ValueError), (" \t\n", ValueError),
                             (None, TypeError), (123, TypeError), (True, TypeError)]:
            with self.subTest(value=value):
                # Arrange / Act / Assert
                with self.assertRaises(error):
                    self.make_samovar(name=value)

    def test_TC_M_04_constructor_numeric_types(self):
        """TC_M_04: bool и нечисловые типы запрещены."""
        for name in ("wing_span_m", "max_speed_kmh", "steam"):
            for value in (True, False, "5", None, complex(1, 2)):
                with self.subTest(name=name, value=value):
                    # Arrange / Act / Assert
                    with self.assertRaises(TypeError):
                        self.make_samovar(**{name: value})

    def test_TC_M_05_constructor_numeric_ranges(self):
        """TC_M_05: диапазоны и неконечные числа."""
        invalid = {"wing_span_m": [0, 0.5, 10.1],
                   "max_speed_kmh": [0, 0.5, 120.1], "steam": [-0.1, 100.1]}
        for name, values in invalid.items():
            for value in values + [float("nan"), float("inf"), -float("inf")]:
                with self.subTest(name=name, value=value):
                    # Arrange / Act / Assert
                    with self.assertRaises(ValueError):
                        self.make_samovar(**{name: value})

    def test_TC_M_06_read_only_attributes(self):
        """TC_M_06: запись и удаление публичных атрибутов запрещены."""
        # Arrange
        samovar = self.make_samovar()
        for name, value in self.state(samovar).items():
            with self.subTest(name=name):
                # Act / Assert
                self.assert_unchanged_error(samovar, AttributeError,
                                            lambda: setattr(samovar, name, value))
                self.assert_unchanged_error(samovar, AttributeError,
                                            lambda: delattr(samovar, name))

    def test_TC_M_07_deploy_wings(self):
        """TC_M_07: раскрытие крыльев, повторный вызов на земле и в воздухе."""
        # Arrange
        samovar = self.make_samovar()
        before = self.state(samovar)
        # Act / Assert
        self.assertIsNone(samovar.deploy_wings())
        self.assertEqual(self.state(samovar), before | {"wings_deployed": True})
        for airborne in (False, True):
            if airborne:
                samovar.move(1, "air")
            before = self.state(samovar)
            self.assertIsNone(samovar.deploy_wings())
            self.assertEqual(self.state(samovar), before)

    def test_TC_M_08_fold_wings_on_ground(self):
        """TC_M_08: складывание крыльев на земле, включая повторное."""
        # Arrange
        samovar = self.make_samovar()
        # Act / Assert
        self.assertIsNone(samovar.fold_wings())
        samovar.deploy_wings()
        before = self.state(samovar)
        self.assertIsNone(samovar.fold_wings())
        self.assertEqual(self.state(samovar), before | {"wings_deployed": False})
        before = self.state(samovar)
        self.assertIsNone(samovar.fold_wings())
        self.assertEqual(self.state(samovar), before)

    def test_TC_M_09_fold_wings_in_flight(self):
        """TC_M_09: в полёте крылья не складываются."""
        # Arrange
        samovar = self.make_samovar()
        samovar.deploy_wings()
        samovar.move(1, "air")
        # Act / Assert
        self.assert_unchanged_error(samovar, self.module.SamovarInFlight,
                                    samovar.fold_wings)

    def test_TC_M_10_land(self):
        """TC_M_10: посадка на пустом баке и повторная посадка."""
        # Arrange
        samovar = self.make_samovar(steam=2)
        before = self.state(samovar)
        self.assertIsNone(samovar.land())
        self.assertEqual(self.state(samovar), before)
        samovar.deploy_wings()
        samovar.move(1, "air")
        before = self.state(samovar)
        # Act
        result = samovar.land()
        # Assert
        self.assertIsNone(result)
        self.assertEqual(self.state(samovar), before | {"is_flying": False})
        before = self.state(samovar)
        self.assertIsNone(samovar.land())
        self.assertEqual(self.state(samovar), before)

    def test_TC_M_11_normal_flight(self):
        """TC_M_11: обычный полёт, дробная дистанция и накопление пути."""
        # Arrange
        samovar = self.make_samovar()
        samovar.deploy_wings()
        before = self.state(samovar)
        # Act
        first = samovar.move(distance_km=10, terrain="air")
        second = samovar.move(0.25, "air")
        # Assert
        self.assert_result(first, 0.25)
        self.assert_result(second, 0.00625)
        self.assertEqual(self.state(samovar), before | {
            "steam": 79.5, "position_km": 10.25, "is_flying": True})

    def test_TC_M_12_headwind(self):
        """TC_M_12: ветер уменьшает скорость и повышает расход."""
        # Arrange
        samovar = self.make_samovar()
        samovar.deploy_wings()
        before = self.state(samovar)
        # Act
        result = samovar.move(10, "headwind")
        # Assert
        self.assert_result(result, 0.5)
        self.assertEqual(self.state(samovar), before | {
            "steam": 70.0, "position_km": 10.0, "is_flying": True})

    def test_TC_M_13_exact_steam(self):
        """TC_M_13: точного запаса хватает, автоматической посадки нет."""
        for terrain, steam in [("air", 20), ("headwind", 30)]:
            with self.subTest(terrain=terrain):
                # Arrange
                samovar = self.make_samovar(steam=steam)
                samovar.deploy_wings()
                # Act
                result = samovar.move(10, terrain)
                # Assert
                self.assert_result(result, 0.25 if terrain == "air" else 0.5)
                self.assertEqual(samovar.steam, 0.0)
                self.assertEqual(samovar.position_km, 10.0)
                self.assertIs(samovar.is_flying, True)
                self.assert_unchanged_error(samovar, self.module.SamovarNotEnoughSteam,
                                            lambda: samovar.move(0.25, terrain))

    def test_TC_M_14_not_enough_steam(self):
        """TC_M_14: нехватка пара не меняет состояние."""
        cases = [("air", 5, 3), ("headwind", 8.99999999, 3),
                 ("air", 100, 100)]
        for terrain, steam, distance in cases:
            with self.subTest(terrain=terrain, distance=distance):
                # Arrange
                samovar = self.make_samovar(steam=steam)
                samovar.deploy_wings()
                # Act / Assert
                self.assert_unchanged_error(samovar, self.module.SamovarNotEnoughSteam,
                                            lambda: samovar.move(distance, terrain))

    def test_TC_M_15_wings_folded(self):
        """TC_M_15: полёт требует раскрытых крыльев."""
        # Arrange
        samovar = self.make_samovar()
        # Act / Assert
        self.assert_unchanged_error(samovar, self.module.SamovarWingsFolded,
                                    lambda: samovar.move(1, "air"))

    def test_TC_M_16_forbidden_terrain(self):
        """TC_M_16: вода и земля запрещены."""
        # Arrange
        samovar = self.make_samovar()
        for terrain in ("ground", "water"):
            with self.subTest(terrain=terrain):
                # Act / Assert
                self.assert_unchanged_error(samovar, self.module.SamovarCannotMoveHere,
                                            lambda: samovar.move(1, terrain))

    def test_TC_M_17_invalid_move_arguments(self):
        """TC_M_17: неверные дистанция и среда."""
        # Arrange
        samovar = self.make_samovar()
        invalid = [(v, TypeError) for v in (True, False, "1", None, complex(1, 2))]
        invalid += [(v, ValueError) for v in (0, -1, 100.1, float("nan"),
                                            float("inf"), -float("inf"))]
        for value, error in invalid:
            with self.subTest(distance=value):
                # Act / Assert
                self.assert_unchanged_error(samovar, error,
                                            lambda: samovar.move(value, "air"))
        for value, error in [("AIR", ValueError), (" air", ValueError),
                             ("", ValueError), (None, TypeError), (1, TypeError)]:
            with self.subTest(terrain=value):
                self.assert_unchanged_error(samovar, error,
                                            lambda: samovar.move(1, value))

    def test_TC_M_18_move_error_order(self):
        """TC_M_18: порядок проверки нескольких ошибок."""
        # Arrange
        samovar = self.make_samovar(steam=0)
        cases = [(0, "water", ValueError), (True, None, TypeError),
                 (1, "unknown", ValueError), (1, "water", self.module.SamovarCannotMoveHere),
                 (1, "air", self.module.SamovarWingsFolded)]
        for distance, terrain, error in cases:
            with self.subTest(distance=distance, terrain=terrain):
                # Act / Assert
                self.assert_unchanged_error(samovar, error,
                                            lambda: samovar.move(distance, terrain))

    def test_TC_M_19_calculate_energy(self):
        """TC_M_19: расчёт независим от крыльев, полёта и запаса пара."""
        for airborne in (False, True):
            # Arrange
            samovar = self.make_samovar(steam=2 if airborne else 0)
            if airborne:
                samovar.deploy_wings()
                samovar.move(1, "air")
            before = self.state(samovar)
            # Act / Assert
            for distance, terrain, expected in [(0.25, "air", 0.5),
                                                  (10, "headwind", 30),
                                                  (100, "air", 200)]:
                self.assert_result(samovar.calculate_energy(
                    distance_km=distance, terrain=terrain), expected)
                self.assertEqual(self.state(samovar), before)

    def test_TC_M_20_invalid_calculation(self):
        """TC_M_20: расчёт проверяет аргументы и запрещённые среды."""
        # Arrange
        samovar = self.make_samovar()
        cases = [(True, "air", TypeError), ("1", "air", TypeError),
                 (None, "air", TypeError), (complex(1, 2), "air", TypeError),
                 (0, "water", ValueError), (-1, "air", ValueError),
                 (100.1, "air", ValueError), (float("nan"), "air", ValueError),
                 (float("inf"), "air", ValueError), (-float("inf"), "air", ValueError),
                 (1, "water", self.module.SamovarCannotMoveHere),
                 (1, "ground", self.module.SamovarCannotMoveHere),
                 (1, "AIR", ValueError), (1, " air", ValueError), (1, "", ValueError),
                 (1, None, TypeError), (1, True, TypeError)]
        for distance, terrain, error in cases:
            with self.subTest(distance=distance, terrain=terrain):
                # Act / Assert
                self.assert_unchanged_error(samovar, error,
                    lambda: samovar.calculate_energy(distance, terrain))

    def test_TC_M_21_obstacles(self):
        """TC_M_21: препятствия на земле, в полёте и при размахе ровно 2 м."""
        for span in (1.5, 2, 2.5):
            # Arrange
            samovar = self.make_samovar(wing_span_m=span)
            for airborne in (False, True):
                if airborne:
                    samovar.deploy_wings()
                    samovar.move(1, "air")
                before = self.state(samovar)
                # Act / Assert
                for obstacle, expected in [("fence", airborne and span >= 2),
                                           ("river", airborne), ("storm", False)]:
                    with self.subTest(span=span, airborne=airborne, obstacle=obstacle):
                        self.assertIs(samovar.can_overcome(obstacle=obstacle), expected)
                        self.assertEqual(self.state(samovar), before)
                for value, error in [("wall", ValueError), ("FENCE", ValueError),
                                     (" fence", ValueError), (None, TypeError), (1, TypeError)]:
                    self.assert_unchanged_error(samovar, error,
                                                lambda: samovar.can_overcome(value))

    def test_TC_M_22_refuel(self):
        """TC_M_22: дробная заправка, предел запаса и неверные аргументы."""
        # Arrange
        samovar = self.make_samovar(steam=60)
        before = self.state(samovar)
        # Act / Assert
        self.assertIsNone(samovar.refuel(amount=0.25))
        self.assertEqual(self.state(samovar), before | {"steam": 60.25})
        self.assertIs(type(samovar.steam), float)
        self.assertIsNone(samovar.refuel(1000))
        self.assertEqual(self.state(samovar), before | {"steam": 100.0})
        before = self.state(samovar)
        self.assertIsNone(samovar.refuel(1))
        self.assertEqual(self.state(samovar), before)
        cases = [(v, TypeError) for v in (True, False, "1", None, complex(1, 2))]
        cases += [(v, ValueError) for v in (0, -1, 1000.1, float("nan"),
                                          float("inf"), -float("inf"))]
        for value, error in cases:
            with self.subTest(value=value):
                self.assert_unchanged_error(samovar, error,
                                            lambda: samovar.refuel(value))

    def test_TC_M_23_refuel_in_flight(self):
        """TC_M_23: заправка в полёте запрещена, аргумент проверяется первым."""
        # Arrange
        samovar = self.make_samovar()
        samovar.deploy_wings()
        samovar.move(1, "air")
        for amount, error in [(1, self.module.SamovarInFlight),
                              (0, ValueError), (True, TypeError)]:
            with self.subTest(amount=amount):
                # Act / Assert
                self.assert_unchanged_error(samovar, error,
                                            lambda: samovar.refuel(amount))

    def test_TC_M_24_status_snapshot(self):
        """TC_M_24: снимок содержит все поля и не связан с объектом."""
        # Arrange
        samovar = self.make_samovar()
        for airborne in (False, True):
            if airborne:
                samovar.deploy_wings()
                samovar.move(1, "air")
            before = self.state(samovar)
            # Act
            first = samovar.get_status()
            second = samovar.get_status()
            # Assert
            self.assertIs(type(first), dict)
            self.assertEqual(first, before)
            self.assertIsNot(first, second)
            for key, value in before.items():
                self.assertIs(type(first[key]), type(value))
            first["steam"] = -1
            first["extra"] = "test"
            self.assertEqual(second, before)
            self.assertEqual(samovar.get_status(), before)
            self.assertEqual(self.state(samovar), before)
