"""Polygon reduction algorithm using the characteristic shape."""

import heapq
from dataclasses import dataclass, field
from typing import Optional

from scipy.spatial import Delaunay

from polyshell.geometry import Line, Polygon


@dataclass(order=True)
class EdgeScore:
    """A score for an edge in the characteristic shape algorithm."""

    sort_index: float = field(init=False)
    score: float
    simplex_id: int
    coprime: int

    def __post_init__(self):
        self.sort_index = -self.score


def reduce_polygon_charshape(
    polygon: Polygon,
    epsilon: float = float("inf"),
    max_loss: float = float("inf"),
    max_length: Optional[int] = None,
) -> Polygon:
    """Reduce a polygon while retaining coverage."""
    if max_length is None:
        max_length = len(polygon)

    return char_shape(polygon, epsilon, max_loss, max_length)


def char_shape(
    orig: Polygon,
    epsilon: float,
    max_loss: float,
    max_length: int,
) -> Polygon:
    """Characteristic shape reduction algorithm."""
    tri = Delaunay(orig.to_array())
    simplices: list[tuple[int, int, int]] = tri.simplices  # type: ignore
    neighbors: list[tuple[int, int, int]] = tri.neighbors  # type: ignore

    boundary_edges: list[tuple[int, int]] = []
    for simplex_id, (simplex, edge_neighbors) in enumerate(zip(simplices, neighbors)):
        for coprime, neighbor in enumerate(edge_neighbors):
            if neighbor == -1:
                boundary_edges.append((simplex_id, coprime))

    boundary_nodes = {
        simplices[simplex_id][(coprime + 1) % 3]
        for simplex_id, coprime in boundary_edges
    }  # simplices are always ordered CCW, so this is okay

    pq = [
        EdgeScore(
            score=get_edge(orig, simplices[simplex_id], coprime).length(),
            simplex_id=simplex_id,
            coprime=coprime,
        )
        for simplex_id, coprime in boundary_edges
    ]
    heapq.heapify(pq)

    loss = 0.0
    while len(pq) and len(boundary_nodes) < max_length:
        largest = heapq.heappop(pq)

        if largest.score < epsilon:
            break

        loss += largest.score
        if loss > max_loss:
            break

        # Regularity check
        simplex = simplices[largest.simplex_id]
        coprime_node = simplex[largest.coprime]
        start, end = get_edge_nodes(simplex, largest.coprime)

        if coprime_node in boundary_nodes:
            continue
        if (start - end) in [-1, 1]:
            continue

        # Update boundary nodes and edges
        boundary_nodes.add(coprime_node)
        recompute_boundary(
            orig, largest.simplex_id, largest.coprime, simplices, neighbors, pq
        )

    # Extract boundary points
    boundary_nodes = sorted(boundary_nodes)
    return Polygon([orig[node] for node in boundary_nodes] + [orig[boundary_nodes[0]]])


# TODO: Is there a more elegant way to do this?
def get_edge(orig: Polygon, simplex: tuple[int, int, int], coprime: int) -> Line:
    """Return an edge from a simplex given its corresponding coprime node."""
    start, end = get_edge_nodes(simplex, coprime)
    return Line((orig[start], orig[end]))


def get_edge_nodes(simplex: tuple[int, int, int], coprime: int) -> tuple[int, int]:
    """Return an edge from a simplex given its corresponding coprime node."""
    return simplex[(coprime + 1) % 3], simplex[(coprime + 2) % 3]


def recompute_boundary(
    orig: Polygon,
    simplex_id: int,
    coprime: int,
    simplices: list[tuple[int, int, int]],
    neighbors: list[tuple[int, int, int]],
    pq: list[EdgeScore],
):
    """Reveal two new edges by the removal of another."""
    simplex = simplices[simplex_id]
    for node in range(3):
        if node == coprime:
            continue

        new_simplex_id = neighbors[simplex_id][node]
        for new_coprime, neighbor in enumerate(neighbors[new_simplex_id]):
            if neighbor == simplex_id:
                break
        else:
            assert False, "neighbors does not commute"

        score = get_edge(orig, simplex, node).length()
        e = EdgeScore(
            score,
            simplex_id=new_simplex_id,
            coprime=new_coprime,
        )
        heapq.heappush(pq, e)
