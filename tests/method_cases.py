from typing import Callable

from polyshell import reduce_polygon_char, reduce_polygon_rdp, reduce_polygon_vw


def case_char() -> Callable:
    return reduce_polygon_char


def case_rdp() -> Callable:
    return reduce_polygon_rdp


def case_vw() -> Callable:
    return reduce_polygon_vw
