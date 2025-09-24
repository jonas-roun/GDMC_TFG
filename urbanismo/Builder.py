from .HiDesResBuilder import HiDesResBuilder
from .LowDesResBuilder import LowDesResBuilder
from .parcela import Parcela


def get_constructor(parcela: Parcela,uso):
    if uso == "lowDesRes":
        return LowDesResBuilder()
    elif uso == "hiDesRes":
        return HiDesResBuilder()
    else:
        raise ValueError(f"Uso desconocido: {uso}")

