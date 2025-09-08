use geo::{Coord, GeoFloat, LineString, Polygon};
use hashbrown::HashSet;
use spade::handles::{DirectedEdgeHandle, VertexHandle};
use spade::{DelaunayTriangulation, Point2, SpadeNum, Triangulation};
use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::hash::Hash;

#[derive(Debug)]
struct CharScore<'a, T>
where
    T: SpadeNum,
{
    score: T,
    edge: DirectedEdgeHandle<'a, Point2<T>, (), (), ()>,
}

// These impls give us a max-heap
impl<T: SpadeNum> Ord for CharScore<'_, T> {
    fn cmp(&self, other: &CharScore<T>) -> Ordering {
        self.score.partial_cmp(&other.score).unwrap()
    }
}

impl<T: SpadeNum> PartialOrd for CharScore<'_, T> {
    fn partial_cmp(&self, other: &CharScore<T>) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<T: SpadeNum> Eq for CharScore<'_, T> {}

impl<T: SpadeNum> PartialEq for CharScore<'_, T> {
    fn eq(&self, other: &CharScore<T>) -> bool {
        self.score == other.score
    }
}

#[derive(Debug)]
struct BoundaryNode<'a, T>(VertexHandle<'a, Point2<T>>);

impl<T> PartialEq for BoundaryNode<'_, T> {
    fn eq(&self, other: &BoundaryNode<T>) -> bool {
        self.0.index() == other.0.index()
    }
}

impl<T> Eq for BoundaryNode<'_, T> {}

impl<T> Hash for BoundaryNode<'_, T>
where
    T: SpadeNum,
{
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.0.index().hash(state);
    }
}

impl<T> Ord for BoundaryNode<'_, T> {
    fn cmp(&self, other: &BoundaryNode<T>) -> Ordering {
        self.0.index().partial_cmp(&other.0.index()).unwrap()
    }
}

impl<T> PartialOrd for BoundaryNode<'_, T> {
    fn partial_cmp(&self, other: &BoundaryNode<T>) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn characteristic_shape<T>(orig: &Polygon<T>, eps: T, max_len: usize) -> Polygon<T>
where
    T: GeoFloat + SpadeNum,
{
    // Construct Delaunay triangulation
    let vertices = orig
        .exterior()
        .coords()
        .map(|c| Point2::new(c.x, c.y))
        .collect::<Vec<_>>();
    let tri = DelaunayTriangulation::<Point2<T>>::bulk_load_stable(vertices).unwrap();

    let boundary_edges = tri.convex_hull().map(|edge| edge.rev()).collect::<Vec<_>>();
    let mut boundary_nodes: HashSet<_> =
        HashSet::from_iter(boundary_edges.iter().map(|&edge| BoundaryNode(edge.from())));

    let mut pq = boundary_edges
        .iter()
        .map(|&line| CharScore {
            score: line.length_2(), // TODO: this is the squared length
            edge: line,
        })
        .collect::<BinaryHeap<_>>();

    while let Some(largest) = pq.pop() {
        if largest.score < eps || boundary_nodes.len() >= max_len {
            break;
        }

        // Regularity check
        let coprime_node = BoundaryNode(largest.edge.opposite_vertex().unwrap());
        if boundary_nodes.contains(&coprime_node) {
            continue;
        }

        let [from, to] = largest.edge.vertices().map(|v| v.index());
        if (to == from + 1) || (from == to + 1) {
            continue;
        }

        // Update boundary nodes and edges
        boundary_nodes.insert(coprime_node);
        recompute_boundary(largest.edge, &mut pq);
    }

    // Extract boundary nodes
    let mut boundary_nodes = boundary_nodes.drain().collect::<Vec<_>>();
    boundary_nodes.sort();

    let exterior = LineString::from_iter(boundary_nodes.into_iter().map(|n| {
        let p = n.0.position();
        Coord { x: p.x, y: p.y }
    }));
    Polygon::new(exterior, vec![])
}

fn recompute_boundary<'a, T>(
    edge: DirectedEdgeHandle<'a, Point2<T>, (), (), ()>,
    pq: &mut BinaryHeap<CharScore<'a, T>>,
) where
    T: GeoFloat + SpadeNum,
{
    //
    let choices = [edge.prev(), edge.next()];
    for new_edge in choices {
        let e = CharScore {
            score: new_edge.length_2(),
            edge: new_edge.rev(),
        };
        pq.push(e);
    }
}

pub trait SimplifyCharshape<T, Epsilon = T> {
    fn simplify_charshape(&self, eps: Epsilon, len: usize) -> Self;
}

impl<T> SimplifyCharshape<T> for Polygon<T>
where
    T: GeoFloat + SpadeNum,
{
    fn simplify_charshape(&self, eps: T, len: usize) -> Self {
        characteristic_shape(self, eps, len - 1)
    }
}
