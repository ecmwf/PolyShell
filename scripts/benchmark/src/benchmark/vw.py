"""Benchmarks for Visvalingam-Whyatt."""

from polyshell import reduce_polygon
from simplification.cutil import simplify_coords_vwp


def polyshell_vw(poly, eps):
    return reduce_polygon(poly, "epsilon", eps, method="vw")


def simplification_vw(poly, eps):
    return simplify_coords_vwp(poly, eps)


RUNNERS = [polyshell_vw, simplification_vw]
LABELS = ["polyshell (vw)", "simplification"]

BENCHMARKS = list(zip(RUNNERS, LABELS))
