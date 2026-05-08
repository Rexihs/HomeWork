from scr.reservoir import Reservoir, ResProps
from scr.well import Well
from scr.pipe import Pipe
from scr.compressor import DCS
from scr.state import NodeState
import scipy
import pandas as pd

class FieldSimulator:
    def __init__(self, 
        reservoir: Reservoir,
        respops: ResProps,
        wells: list,      # список из 3 объектов Well
        shlyf: Pipe,
        dcs: DCS
        ):
        
        """
        Класс для расчёта динамики добычи и давления в пласте

        Параметры
        ----------
        reservoir - класс для расчёта материального баланса
        wells - список из 3 объектов класса Well
        shlyf - класс для расчёта dp (pipe)
        dcs - класс для расчёта давления на входе в ДКС и расхода газа на выходе из ДКС
        """
        self.reservoir = reservoir
        self.wells = wells
        self.shlyf = shlyf
        self.dcs = dcs

    def solve(self, P_res: float) -> dict[str, NodeState]:
        """
        Решение системы явным методом

        P_res: Пластовое давление (атм)
        """
        # возвращает словарь NodeState по именам элементов:
        # 'well_1', 'well_2', 'well_3', 'shlyf', 'dcs'

        # Расчёт таких параметров сети что бы DKS_out == P_line:
        # well (bhp[]) -> wellbore (thp,q) -> (Pman - точка соединения скважин, начала pipe.out) pipe.out_P (sflu(P_man,q)) -> DKS (thp_in,q)
        # Проверка выполнения DKS == P_line

        def system(x):
            """
            input:
            list BHP по скважинам,
            Давление на манифольде между скважинами, (атм)

            output:
            (P_man - P)
            """
            BHP = x[:len(self.wells)] # list забойных давление по скважинам, (атм)
            P_man = x[-1] # давление на манифольде между скважинами, (атм)

            q_wells = []
            THP = []

            # Расчёт дебитов и устьевого давления по скважинам
            for i, well in enumerate(self.wells):
                qi = well.q(P_res, BHP[i])
                q_wells.append(qi)
                THP_i = well.pipe.pwf_to_wh(BHP[i], qi)
                THP.append(THP_i)

            q_total = sum(q_wells)
            q_shlyf = q_total + self.dcs.q_ext
            P_shlyf_out = self.shlyf.pwf_to_wh(P_man, q_shlyf)

            eqs = [] # Вектор невязок, (1-3 по скв, 4 вход/выход ДКС)
            for i in range(len(self.wells)):
                eqs.append(THP[i] - P_man)

            # 1.первый способ - относительно входа в ДКС
            # eqs.append(P_shlyf_out - self.dcs.P_in())

            # 2.второй способ - относительно выхода из ДКС
            P_DCS_out = self.dcs.P_out(P_shlyf_out,q_shlyf) # Берём давление на выходе из шлейфа
            eqs.append(P_DCS_out - self.dcs.P_line)

            return eqs

        P_man = self.dcs.P_in()+5 # Начальное приблежение давление на манифольде
        # начальное приближение забойного давления по сквжинам
        x0 = []
        for well in self.wells:
            c = well.C(P_res)
            x0.append(P_res - 500 / c if c != 0 else P_res - 10)
        x0.append(P_man)

        # Балансировка системы скважин по THP - устьевому давлению и давлению на конечной точке (вход/выход ДКС)
        sol = scipy.optimize.fsolve(system, x0)

        BHP = sol[:len(self.wells)]
        P_man = sol[-1]

        # финальный расчёт
        states = {}

        q_total = 0

        for i, well in enumerate(self.wells):
            qi = well.q(P_res, BHP[i])
            if qi < 0:
                qi = 0
            q_total += qi

            THP = well.pipe.pwf_to_wh(BHP[i], qi)

            states[f'well_{i+1}'] = NodeState(
                name=f'well_{i+1}',
                # P_in=P_res, # Пластовое давление
                P_in=BHP[i], # Забойное давление
                P_out=THP,
                dP=BHP[i] - THP,
                q_std=qi,
                q_res=None,
                v=None,
                rho=None
            )

        q_shlyf = q_total + self.dcs.q_ext
        P_shlyf_out = self.shlyf.pwf_to_wh(P_man, q_shlyf)
        P_dcs_in = P_shlyf_out # Давление на входе равно давлению на выходе из шлейфа
        P_dcs_out = self.dcs.P_out(P_dcs_in, q_shlyf) # Давление на выходе из ДКС

        states['shlyf'] = NodeState(
            name='shlyf',
            P_in=P_man,
            P_out=P_shlyf_out,
            dP=P_man - P_shlyf_out,
            q_std=q_shlyf,
            q_res=None,
            v=None,
            rho=None
        )

        states['dcs'] = NodeState(
            name='dcs',
            P_in=P_dcs_in,
            P_out=P_dcs_out,
            dP=P_dcs_out - P_dcs_in,
            q_std=q_shlyf,
            q_res=None,
            v=None,
            rho=None
        )

        return states

    def run(self, N_days: int, dt: float = 1.0) -> pd:
        # колонки: t [сут], P_res [атм], P_man [атм],
        #          q1, q2, q3, q_total [ст.м³/сут], Gp [тыс.ст.м³]
        
        pass
