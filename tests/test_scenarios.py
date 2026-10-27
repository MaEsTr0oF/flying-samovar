from tests.pilot import Pilot
from tests.support import SamovarTestCase


class SamovarScenarios(SamovarTestCase):
    def test_TC_S_01_tea_trip(self):
        """TC_S_01: поездка за чаем, два участка и посадка."""
        # Given
        samovar = self.make_samovar()
        pilot = Pilot(samovar)
        # When
        pilot.prepare()
        first = pilot.fly(10)
        second = pilot.fly(5)
        # Then
        self.assert_result(first, 0.25)
        self.assert_result(second, 0.125)
        self.assert_result(samovar.steam, 70.0)
        self.assert_result(samovar.position_km, 15.0)
        self.assertIs(samovar.is_flying, True)
        # When
        pilot.land()
        pilot.pack_wings()
        # Then
        self.assertIs(samovar.is_flying, False)
        self.assertIs(samovar.wings_deployed, False)
        self.assert_result(samovar.steam, 70.0)
        self.assert_result(samovar.position_km, 15.0)

    def test_TC_S_02_windy_return(self):
        """TC_S_02: спокойный участок, ветер и река."""
        # Given
        samovar = self.make_samovar(steam=90)
        pilot = Pilot(samovar)
        # When
        pilot.prepare()
        first = pilot.fly(10)
        second = pilot.fly_against_wind(10)
        # Then
        self.assert_result(first, 0.25)
        self.assert_result(second, 0.5)
        self.assert_result(samovar.steam, 40.0)
        self.assert_result(samovar.position_km, 20.0)
        before = self.state(samovar)
        self.assertIs(pilot.check_obstacle("river"), True)
        self.assertEqual(self.state(samovar), before)
        # When
        pilot.land()
        pilot.pack_wings()
        # Then
        self.assertEqual(self.state(samovar), before | {
            "is_flying": False, "wings_deployed": False})

    def test_TC_S_03_not_enough_steam(self):
        """TC_S_03: неудачный старт, заправка и продолжение пути."""
        # Given
        samovar = self.make_samovar(steam=5)
        pilot = Pilot(samovar)
        pilot.prepare()
        # When / Then
        self.assert_unchanged_error(samovar, self.module.SamovarNotEnoughSteam,
                                    lambda: pilot.fly(3))
        # When
        pilot.refill(1)
        first = pilot.fly(3)
        # Then
        self.assert_result(first, 0.075)
        self.assert_result(samovar.steam, 0.0)
        self.assertIs(samovar.is_flying, True)
        # When
        pilot.land()
        pilot.refill(10)
        pilot.fly(1)
        # Then
        self.assert_result(samovar.steam, 8.0)
        self.assert_result(samovar.position_km, 4.0)
        self.assertIs(samovar.is_flying, True)

    def test_TC_S_04_refill_after_landing(self):
        """TC_S_04: действия в воздухе запрещены, на земле разрешены."""
        # Given
        samovar = self.make_samovar(steam=30)
        pilot = Pilot(samovar)
        # When
        pilot.prepare()
        pilot.fly(5)
        # Then
        self.assert_result(samovar.steam, 20.0)
        self.assert_result(samovar.position_km, 5.0)
        self.assert_unchanged_error(samovar, self.module.SamovarInFlight,
                                    pilot.pack_wings)
        self.assert_unchanged_error(samovar, self.module.SamovarInFlight,
                                    lambda: pilot.refill(1))
        # When
        pilot.land()
        pilot.refill(0.25)
        pilot.pack_wings()
        pilot.prepare()
        time = pilot.fly_against_wind(0.125)
        # Then
        self.assert_result(time, 0.00625)
        self.assert_result(samovar.steam, 19.875)
        self.assert_result(samovar.position_km, 5.125)
        self.assertIs(samovar.is_flying, True)

    def test_TC_S_05_fence_and_river(self):
        """TC_S_05: доступность препятствий меняется после взлёта и посадки."""
        # Given
        samovar = self.make_samovar(wing_span_m=2, steam=20)
        pilot = Pilot(samovar)
        before = self.state(samovar)
        for obstacle in ("fence", "river", "storm"):
            self.assertIs(pilot.check_obstacle(obstacle), False)
        self.assertEqual(self.state(samovar), before)
        # When
        pilot.prepare()
        pilot.fly(1)
        # Then
        before = self.state(samovar)
        self.assertIs(pilot.check_obstacle("fence"), True)
        self.assertIs(pilot.check_obstacle("river"), True)
        self.assertIs(pilot.check_obstacle("storm"), False)
        self.assertEqual(self.state(samovar), before)
        self.assert_result(samovar.steam, 18.0)
        self.assert_result(samovar.position_km, 1.0)
        # When
        pilot.land()
        # Then
        before = self.state(samovar)
        for obstacle in ("fence", "river", "storm"):
            self.assertIs(pilot.check_obstacle(obstacle), False)
        self.assertEqual(self.state(samovar), before)

    def test_TC_S_06_empty_tank_landing(self):
        """TC_S_06: нулевой запас не мешает сесть и начать новый полёт."""
        # Given
        samovar = self.make_samovar(steam=20)
        pilot = Pilot(samovar)
        # When
        pilot.prepare()
        pilot.fly(10)
        # Then
        self.assert_result(samovar.steam, 0.0)
        self.assert_result(samovar.position_km, 10.0)
        self.assertIs(samovar.is_flying, True)
        self.assert_unchanged_error(samovar, self.module.SamovarNotEnoughSteam,
                                    lambda: pilot.fly(0.5))
        # When
        pilot.land()
        pilot.pack_wings()
        pilot.refill(20)
        pilot.prepare()
        time = pilot.fly_against_wind(5)
        pilot.land()
        # Then
        self.assert_result(time, 0.25)
        self.assert_result(samovar.steam, 5.0)
        self.assert_result(samovar.position_km, 15.0)
        self.assertIs(samovar.wings_deployed, True)
        self.assertIs(samovar.is_flying, False)
