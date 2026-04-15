from scr.reservoir import Reservoir, ResProps
from scr.well import Well
from scr.pipe import Pipe
from scr.compressor import DCS
from scr.state import NodeState

class FieldSimulator:
    def __init__(self,
        reservoir: Reservoir,
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
        # возвращает словарь NodeState по именам элементов:
        # 'well_1', 'well_2', 'well_3', 'shlyf', 'dcs'
        pass

    def run(self, N_days: int, dt: float = 1.0) -> DataFrame:
        # колонки: t [сут], P_res [атм], P_man [атм],
        #          q1, q2, q3, q_total [ст.м³/сут], Gp [тыс.ст.м³]
        pass