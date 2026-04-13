import numpy as np
from scr.fluid import Fluid
from scr.pipe import Pipe
from scr.reservoir import ResProps

class Well:
    def __init__(self, fluid: Fluid, k: float, h: float, re: float, rw: float, pipe: Pipe = None):
        """
        Класс для расчёта расчитывающий дебит скважины и объеденяющи приток из
        пласта с VLP кривой

        Параметры
        ----------
        Fluid [class] - модель флюида
        k [мД] - проницаемость
        h [м] - эффективная толщина пласта
        re [м] - радиус скважины
        rw [м] - радиус контура питания
        pipe [class] - модель скважины
        """

        self.fluid = fluid
        self.k = k
        self.h = h
        self.re = re
        self.rw = rw
        self.pipe = pipe

    def C(self, P_res: float) -> float:
        """
        Коэффициента продуктивности скважины
        b*k*h / (mu * ln(re/rw))

        Параметры
        ----------
        P_res [атм] - пластовое давление
        """

        beta = 0.00852702 # Переводной коэффициент
        mu = self.fluid.get_mu(P_res)

        # В случае квадратичного закона фильтрации для газа:
        # z = self.fluid.get_z(P_res)
        # return beta * self.k * self.h / (mu * z * np.log(self.re / self.rw))

        return beta * self.k * self.h / (mu * np.log(self.re / self.rw))

    def q(self, P_res, P_bhp: float) -> float:
        """
        Расчёт дебита скважины
        q = c * (▲P), ст. м3/сут

        Параметры
        ----------s
        P_res [атм] - пластовое давление
        P_bhp [атм] - забойное давление
        """

        C = self.C(P_res)

        # В случае квадратичного закона фильтрации для газа:
        # return C * (P_res**2 - P_bhp**2)

        return C * (P_res - P_bhp)

    def bhp(self, THP: float, q_std: float) -> float:
        """
        Расчёт забойного давления через устьевое
        BHP = THP + Dp_pipe

        Параметры
        ----------
        THP [атм] - устьевое давление
        q_std [м3/сут] - дебит в ст. условиях
        """

        state = self.pipe.dp(THP, q_std)

        return THP + state.dP

    def ipr_curve(self, P_res: float, n_points: int = 20):
        """
        Построение IPR-кривой

        Параметры
        ----------
        P_res [атм] - пластовое давление
        n_points = 20 [шт] - количество точек кривой
        """

        bhp_point = np.linspace(0, P_res, n_points)
        q_std = [self.q(P_res, bhp) for bhp in bhp_point]

        return bhp_point, q_std