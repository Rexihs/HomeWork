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
        self.prev_solution = None # Начальное приблежение с прошлого шага

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

            # Ограничения по забойному давлению
            for i in range(len(BHP)):
            
                if BHP[i] < 1:
                    return [1e6] * (len(self.wells) + 1)

                if BHP[i] > P_res:
                    return [1e6] * (len(self.wells) + 1)

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

        if self.prev_solution is None:

            x0 = []
            for well in self.wells:
                # x0.append(P_res * 0.9) # Для квадратичного закона
                c = well.C(P_res)
                x0.append(P_res - 500 / c if c != 0 else P_res - 10)

            P_man0 = self.dcs.P_in() + 5
            x0.append(P_man0)

        else:
            x0 = self.prev_solution # Берём решение с прошлого шага

        # Балансировка системы скважин по THP - устьевому давлению и давлению на конечной точке (вход/выход ДКС)
        # sol = scipy.optimize.fsolve(system, x0)

        lower_bounds = [1] * len(self.wells) + [1]
        upper_bounds = [P_res] * len(self.wells) + [P_res]

        result = scipy.optimize.least_squares(
            system,
            x0,
            bounds=(lower_bounds, upper_bounds),
            method='trf'
        )

        # Сохраняем решение для следующего шага
        self.prev_solution = result.x
        sol = result.x

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

    def run(self, N_days: int, dt: float = 1.0) -> pd.DataFrame:
        # колонки: t [сут], P_res [атм], P_man [атм],
        #          q1, q2, q3, q_total [ст.м³/сут], Gp [тыс.ст.м³]
        results = []
        states_result = []
        Gp = 0.0
        n_steps = int(N_days / dt)

        for step in range(n_steps):
            t = step * dt
            P_res = self.reservoir.resprops.P

            states = self.solve(P_res)
            states_result.append(states)

            q1 = states['well_1'].q_std
            q2 = states['well_2'].q_std
            q3 = states['well_3'].q_std

            # Проверка на отрицательность дебита, если так q==0
            q1 = max(0.0, q1)
            q2 = max(0.0, q2)
            q3 = max(0.0, q3)

            q_total = q1 + q2 + q3
            q_dcs = states['dcs'].q_std
            P_man = states['shlyf'].P_in
            Gp += q_total * dt

            results.append({
                't': t,
                'P_res': P_res,
                'P_man': P_man,

                'q1': q1,
                'q2': q2,
                'q3': q3,

                'q_total': q_total,
                'q_dcs': q_dcs,

                'Gp': Gp
                })

            P_new = self.reservoir.p2(q_total, dt=dt)
            self.reservoir.resprops.P = P_new

        df = pd.DataFrame(results)
        df_states = pd.DataFrame(states_result)
        return df, df_states
