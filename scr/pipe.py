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
    
    def pwf_to_wh(self, P_bhp, q_std):
        """
        Расчёт устьевого давления по Дарси–Вейсбаху
        интегрирование BHP to THP

        P_bhp [атм] - забойное давление
        q_std [ст.м3/сут]
        """
        P = float(P_bhp)

        dl = 100
        n_steps = int(self.L // dl)
        if self.L % dl != 0:
            n_steps += 1

        for i in range(n_steps):

            # длина участка
            if i == n_steps - 1:
                dl_i = self.L - dl * (n_steps - 1)
            else:
                dl_i = dl

            # вертикальная составляющая
            dz = dl_i * (self.vertical_depth / self.L)

            # свойства при текущем давлении (ВАЖНО!)
            ro = self.fluid.get_ro(P)
            Bg = self.fluid.get_bg(P)
            mu = self.fluid.get_mu(P) * 1e-3

            # скорость
            A = np.pi * self.D**2 / 4
            u = q_std / 86400 * Bg / A

            Re = ro * u * self.D / mu

            # коэффициент трения
            if Re < 2300:
                lyambda = 64 / Re
            else:
                def colebrook_eq(lmbd):
                    return 1/np.sqrt(lmbd) + 2*np.log10(
                        self.roughness/(3.7*self.D) + 2.51/(Re*np.sqrt(lmbd))
                    )
                
                lyambda = scipy.optimize.fsolve(colebrook_eq, 0.02)[0]

            # потери давления
            dp_fric = lyambda * (dl_i / self.D) * (ro * u**2 / 2)
            dp_grav = ro * 9.80665 * dz

            dp_i = (dp_fric + dp_grav) / 101325  # атм

            P -= dp_i
            P = float(P)

        return P  # THP

    def dp(self, THP, q_std):

        def func(P_bhp):
            P_bhp = float(P_bhp)
            P_wh_calc = self.pwf_to_wh(P_bhp, q_std)
            return P_wh_calc - THP

        P_bhp_guess = THP + 50  # старт

        P_bhp = scipy.optimize.fsolve(func, P_bhp_guess)[0]

        return P_bhp - THP