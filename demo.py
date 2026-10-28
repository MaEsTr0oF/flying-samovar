"""Демо летающего самовара. Запуск: python3 demo.py."""

from flying_samovar import FlyingSamovar, SamovarWingsFolded, SamovarInFlight, SamovarNotEnoughSteam


def main():
    samovar = FlyingSamovar("Пых", wing_span_m=2.5, max_speed_kmh=40)
    print("Начало:", samovar.get_status())
    try:
        samovar.move(1, "air")
    except SamovarWingsFolded as error:
        print("Со сложенными крыльями:", type(error).__name__)
    samovar.deploy_wings()
    print("Полёт 10 км, часов:", samovar.move(10, "air"))
    print("Против ветра 10 км, часов:", samovar.move(10, "headwind"))
    print("Забор:", samovar.can_overcome("fence"))
    print("Река:", samovar.can_overcome("river"))
    print("Буря:", samovar.can_overcome("storm"))
    before = samovar.get_status()
    try:
        samovar.refuel(10)
    except SamovarInFlight as error:
        print("Заправка в воздухе:", type(error).__name__)
    print("Состояние после ошибки прежнее:", samovar.get_status() == before)
    print("После проверки бури можно лететь, часов:", samovar.move(5, "air"))
    samovar.land()
    samovar.refuel(60)
    samovar.fold_wings()
    print("После посадки и заправки:", samovar.get_status())

    empty = FlyingSamovar("На полном баке", 2.5, 40)
    empty.deploy_wings()
    print("Полёт 50 км, часов:", empty.move(50, "air"))
    print("Пустой бак, но ещё в воздухе:", empty.steam, empty.is_flying)
    try:
        empty.move(1, "air")
    except SamovarNotEnoughSteam as error:
        print("Следующий полёт:", type(error).__name__)
    empty.land()
    print("После посадки:", empty.is_flying)


if __name__ == "__main__":
    main()
