import json

class ResProps:
    def __init__(self, P: float, V: float, T: float):
        self.P = P  # атм
        self.V = V  # м3
        self.T = T  # К

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4)


class Reservoir:

    def __init__(self, resprops, fluid):
        self.resprops = resprops
        self.fluid = fluid

    def p2(self, q_total: float, dt: float = 1.0) -> float:
        """
        Пластовое давление по материальному балансу Pi+1

        q_total : суммарный дебит (ст.м3/сут)
        dt : шаг по времени (сут)
        """

        P = self.resprops.P
        V = self.resprops.V

        # свойства при текущем давлении
        z = self.fluid.get_z(P)
        rho = self.fluid.get_ro(P)

        # стандартная плотность (константа)
        rho_std = self.fluid.rho_c

        # формула материального баланса
        Pi2 = P - (z * rho_std / rho) * (q_total / V) * dt

        return Pi2