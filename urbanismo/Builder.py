from urbanismo.HiDesResBuilder import HiDesResBuilder
from urbanismo.LowDesResBuilder import LowDesResBuilder


def get_constructor(uso):
    if uso == "lowDesRes":
        return LowDesResBuilder()
    elif uso == "hiDesRes":
        return HiDesResBuilder()
    else:
        raise ValueError(f"Uso desconocido: {uso}")
