class Pilot:
    """Команды пилота для сценарных тестов."""

    def __init__(self, samovar):
        self.samovar = samovar

    def prepare(self):
        return self.samovar.deploy_wings()

    def fly(self, distance_km):
        return self.samovar.move(distance_km, "air")

    def fly_against_wind(self, distance_km):
        return self.samovar.move(distance_km, "headwind")

    def land(self):
        return self.samovar.land()

    def pack_wings(self):
        return self.samovar.fold_wings()

    def refill(self, amount):
        return self.samovar.refuel(amount)

    def check_obstacle(self, obstacle):
        return self.samovar.can_overcome(obstacle)
