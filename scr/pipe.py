import numpy as np
from scr.fluid import Fluid
import scipy

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
        self.fluid = fluid

    def dp(self, THP, q_std):
        """
        Возращает потери давления по системе
        
        Параметры
        ----------
        THP [атм] - давление
        q_std [ст. м3/сут] - объёмный расход газа в ст. условиях
        """

        # FIXME: По хорошему, для дарси-вейсбаха разбить вертикальную скважину 
        # на участки по 100 метров и производить расчёт для каждой части
        # Добавить разбиение по vertical_dept если это не скважина вертикальная составляющая другая

        # Реализация с разбиением на участки по 100 метров

        P = THP # Первая точка, давление = Руст
        dl = 100  # шаг по длине, м
        n_steps = int(self.L // dl) # кол-во шагов

        # Если кол-во шагов не хватает для длины скважины
        if self.L % dl != 0:
            n_steps += 1

        for i in range(n_steps):

            # корректная длина последнего участка, м
            if i == n_steps - 1:
                dl_i = self.L - dl * (n_steps - 1)
            else:
                dl_i = dl

            # вертикальная составляющая, м
            dz = dl_i * (self.vertical_depth / self.L)

            # свойства газа при давлении в точке Pi
            ro = self.fluid.get_ro(P) # кг/м3
            Bg = self.fluid.get_bg(P) # дол.ед.
            mu = self.fluid.get_mu(P) * 1e-3 # Па*с

            u = q_std / 86400 * Bg / (np.pi * self.D**2 / 4) # м/с

            Re = ro * u * self.D / mu

            if Re < 2300: # Пуазейля
                lyambda = 64 / Re
            else: # Колбрука–Уайта
                def colebrook_eq(lmbd):
                    return 1/np.sqrt(lmbd) + 2*np.log10(
                        self.roughness/(3.7*self.D) + 2.51/(Re*np.sqrt(lmbd))
                    )

                lyambda = scipy.optimize.fsolve(colebrook_eq, 0.02)[0]
    
            # потери давления
            dp_fric = lyambda * (dl_i / self.D) * (ro * u**2 / 2) # На трение
            dp_grav = ro * 9.80665 * dz # Гравитационная составляющая
    
            dp_i = (dp_fric + dp_grav) / 101325  # атм
    
            # Давление следующей точке Pi+1
            P += dp_i

        return P

        # # Без разбиения на участки, запасной вариант
        # ro = self.fluid.get_ro(THP) # кг/м3
        # u = q_std/86400 * self.fluid.get_bg(THP) / (np.pi*self.D**2 / 4) # м/с

        # Re = ro*u*self.D / (self.fluid.get_mu(THP)*10**-3)

        # if Re < 2300:
        #     # Формула Пуазейля
        #     lyambda = 64/Re
        # else:
        #     def colebrook_eq(lmbd):
        #         return 1/np.sqrt(lmbd) + 2*np.log10(
        #             self.roughness/(3.7*self.D) + 2.51/(Re*np.sqrt(lmbd))
        #         )

        #     lyambda = scipy.optimize.fsolve(colebrook_eq, 0.02)[0]

        # # Дарси-Вейсбаха dp в СИ [Па]
        # dp = lyambda * (self.L/self.D) * ((ro*u**2)/2) + ro*9.80665*self.vertical_depth

        # return dp/101325