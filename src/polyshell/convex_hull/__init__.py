from polyshell.geometry import Coord, LineString

from .melkman import melkman, melkman_indices  # noqa: F401


def extreme_point(geom: LineString) -> Coord:
    coords_iter = iter(geom)
    max_coord = next(coords_iter)
    for coord in coords_iter:
        if coord[0] > max_coord[0]:
            max_coord = coord

    return max_coord


def extreme_index(geom: LineString) -> int:
    coords_iter = enumerate(geom)
    _, coord = next(coords_iter)
    max_i, max_x = 0, coord[0]
    for i, coord in coords_iter:
        if coord[0] > max_x:
            max_i, max_x = i, coord

    return max_i
