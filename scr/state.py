from dataclasses import asdict, dataclass

@dataclass(slots=True)
class NodeState:
    """
    Универсальное состояние элемента системы.
    """

    name: str
    P_in: float
    P_out: float
    dP: float
    q_std: float
    q_res: float | None
    v: float | None
    rho: float | None

    def get_state(self) -> dict[str, str | float | None]:
        """
        Параметры:
        Name [] - идентификатор элемента ("well_1", "shlyf", "dcs")
        P_in [атм]      - давление на входе [атм]
        P_out [атм]     - давление на выходе [атм]
        dP [атм]        - перепад давления [атм]
        q_std [ст.м³/сут] - коммерческий расход [ст.м³/сут]
        q_res [м³/сут]  - объёмный расход при местных условиях [м³/сут]
        v [м/с]         - скорость потока [м/с]
        rho [кг/м³]     - плотность газа [кг/м³]
        """
        return asdict(self)