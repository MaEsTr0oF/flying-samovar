"""Летающий самовар по SPEC.md версии 1.0."""


class SamovarError(Exception):
    """Общая ошибка самовара."""


class SamovarWingsFolded(SamovarError):
    """Для полёта нужно раскрыть крылья."""


class SamovarNotEnoughSteam(SamovarError):
    """Пара не хватает на весь участок."""


class SamovarCannotMoveHere(SamovarError):
    """Самовар не передвигается по земле и воде."""


class SamovarInFlight(SamovarError):
    """Действие требует посадки."""


def _number(value: float, name: str, minimum: float, maximum: float,
            positive: bool = False) -> float:
    """Проверяет тип и диапазон, затем приводит число к float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be an int or float")

    if positive:
        valid = minimum < value <= maximum
    else:
        valid = minimum <= value <= maximum
    if not valid:
        raise ValueError(f"{name} is outside the allowed range")

    # Диапазон проверяется до преобразования: огромный int даст ValueError.
    # nan и бесконечности тоже не проходят сравнение с конечными границами.
    return float(value)


class FlyingSamovar:
    """Самовар со складными крыльями и запасом пара."""

    def __init__(self, name: str, wing_span_m: float,
                 max_speed_kmh: float, steam: float = 100.0) -> None:
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not name.strip():
            raise ValueError("name must not be empty")

        wing_span = _number(wing_span_m, "wing_span_m", 1, 10)
        speed = _number(max_speed_kmh, "max_speed_kmh", 1, 120)
        reserve = _number(steam, "steam", 0, 100)

        self._name = name
        self._wing_span_m = wing_span
        self._max_speed_kmh = speed
        self._steam = reserve
        self._position_km = 0.0
        self._wings_deployed = False
        self._is_flying = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def wing_span_m(self) -> float:
        return self._wing_span_m

    @property
    def max_speed_kmh(self) -> float:
        return self._max_speed_kmh

    @property
    def steam(self) -> float:
        return self._steam

    @property
    def position_km(self) -> float:
        return self._position_km

    @property
    def wings_deployed(self) -> bool:
        return self._wings_deployed

    @property
    def is_flying(self) -> bool:
        return self._is_flying

    def deploy_wings(self) -> None:
        """Раскрывает крылья, в том числе в полёте."""
        self._wings_deployed = True

    def fold_wings(self) -> None:
        """Складывает крылья после посадки."""
        if self._is_flying:
            raise SamovarInFlight("land before folding the wings")
        self._wings_deployed = False

    def _trip(self, distance_km: float, terrain: str) -> tuple:
        distance = _number(distance_km, "distance_km", 0, 100, positive=True)
        if not isinstance(terrain, str):
            raise TypeError("terrain must be a string")
        if terrain not in ("air", "headwind", "ground", "water"):
            raise ValueError("unknown terrain")
        if terrain in ("ground", "water"):
            raise SamovarCannotMoveHere("samovar can only fly")

        if terrain == "headwind":
            return distance, distance * 3, self._max_speed_kmh / 2
        return distance, distance * 2, self._max_speed_kmh

    def move(self, distance_km: float, terrain: str) -> float:
        """Пролетает весь участок и возвращает время в часах."""
        distance, required, speed = self._trip(distance_km, terrain)
        if not self._wings_deployed:
            raise SamovarWingsFolded("deploy the wings before flying")
        if self._steam < required:
            raise SamovarNotEnoughSteam("not enough steam for this distance")

        elapsed = distance / speed
        self._position_km += distance
        self._steam -= required
        self._is_flying = True
        return elapsed

    def land(self) -> None:
        """Сажает аппарат, сохраняя крылья раскрытыми."""
        self._is_flying = False

    def calculate_energy(self, distance_km: float, terrain: str) -> float:
        """Считает расход, не проверяя готовность к полёту."""
        _, required, _ = self._trip(distance_km, terrain)
        return required

    def can_overcome(self, obstacle: str) -> bool:
        """Проверяет препятствие без изменения состояния."""
        if not isinstance(obstacle, str):
            raise TypeError("obstacle must be a string")
        if obstacle not in ("fence", "river", "storm"):
            raise ValueError("unknown obstacle")
        if obstacle == "fence":
            return self._is_flying and self._wing_span_m >= 2
        if obstacle == "river":
            return self._is_flying
        return False

    def refuel(self, amount: float) -> None:
        """Пополняет запас на земле, не превышая 100 единиц."""
        amount = _number(amount, "amount", 0, 1000, positive=True)
        if self._is_flying:
            raise SamovarInFlight("land before refueling")
        self._steam = min(100.0, self._steam + amount)

    def get_status(self) -> dict:
        """Возвращает независимый снимок публичных атрибутов."""
        return {
            "name": self._name,
            "wing_span_m": self._wing_span_m,
            "max_speed_kmh": self._max_speed_kmh,
            "steam": self._steam,
            "position_km": self._position_km,
            "wings_deployed": self._wings_deployed,
            "is_flying": self._is_flying,
        }
