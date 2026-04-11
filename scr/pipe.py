import numpy as np
from scr.fluid import Fluid

class Pipe:

    def __init__(self, L: float, D: float, roughness: float, fluid: Fluid, vertical_depth: float = 0.0):
        """
        Класс для расчёта перепада давления в скважинах и системе сбора
        Пока возвращает + const

        Парамеры
        ----------
        L [м] - длина dx
        D [м] - диаметр трубы/ствола
        fluid [class] - модель флюида
        vertical_depth [м] - вертикальная глубина если скв. 
        """
        self.L = L
        self.D = D
        self.roughness = roughness
        self.vertical_depth = vertical_depth

    def dp(THP, q_std):
        """
        Возращает потери давления по системе
        """

        dp = np.sqrt(q_std)/100 # Для примера, расчёт dp будет написан позже

        return dp