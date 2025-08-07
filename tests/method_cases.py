from typing import Callable

from polyshell import reduce_polygon_char, reduce_polygon_vw


def case_visvalingam_whyatt() -> Callable:
    return reduce_polygon_vw


def case_charshape() -> Callable:
    return reduce_polygon_char
