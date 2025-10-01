"""Benchmarks for Ramer-Douglas-Peucher."""

import shapely
from polyshell import reduce_polygon


def polyshell_rdp(poly, eps):
    return reduce_polygon(poly, "epsilon", eps, method="rdp")


def shapely_rdp(poly, eps):
    poly = shapely.geometry.Polygon(poly)
    return shapely.simplify(poly, eps, preserve_topology=True).exterior.coords


RUNNERS = [polyshell_rdp, shapely_rdp]
LABELS = ["polyshell (rdp)", "shapely"]

BENCHMARKS = list(zip(RUNNERS, LABELS))
