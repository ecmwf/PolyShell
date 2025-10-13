// Copyright 2025- European Centre for Medium-Range Weather Forecasts (ECMWF)

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// In applying this licence, ECMWF does not waive the privileges and immunities
// granted to it by virtue of its status as an intergovernmental organisation nor
// does it submit to any jurisdiction.

// Copyright 2025- Niall Oswald and Kenneth Martin and Jo Wayne Tan

use geo::{Coord, CoordsIter, GeoFloat, LineString, Polygon};
use hashbrown::HashSet;
use spade::handles::{DirectedEdgeHandle, VertexHandle};
use spade::{CdtEdge, ConstrainedDelaunayTriangulation, Point2, SpadeNum, Triangulation};
use std::cmp::Ordering;
use std::collections::BinaryHeap;
use std::hash::Hash;

#[derive(Debug)]
struct CharScore<'a, T>
where
    T: SpadeNum,
{
    score: T,
    edge: DirectedEdgeHandle<'a, Point2<T>, (), CdtEdge<()>, ()>,
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
struct BoundaryNode<'a, T>(VertexHandle<'a, Point2<T>, (), CdtEdge<()>>);

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
    if orig.exterior().0.len() < 3 {
        return orig.clone();
    }

    let eps_2 = eps * eps;

    // Construct Delaunay triangulation
    let num_vertices = orig.exterior().0.len() - 1;

    let vertices = orig
        .exterior_coords_iter()
        .take(num_vertices) // duplicate points are removed
        .map(|c| Point2::new(c.x, c.y))
        .collect::<Vec<_>>();

    let edges = (0..num_vertices)
        .map(|i| {
            if i == 0 {
                [vertices.len() - 1, i]
            } else {
                [i - 1, i]
            }
        })
        .collect::<Vec<_>>();

    let tri =
        ConstrainedDelaunayTriangulation::<Point2<T>>::bulk_load_cdt(vertices, edges).unwrap();

    let boundary_edges = tri.convex_hull().map(|edge| edge.rev()).collect::<Vec<_>>();
    let mut boundary_nodes: HashSet<_> =
        HashSet::from_iter(boundary_edges.iter().map(|&edge| BoundaryNode(edge.from())));

    let mut pq = boundary_edges
        .iter()
        .map(|&line| CharScore {
            score: line.length_2(),
            edge: line,
        })
        .collect::<BinaryHeap<_>>();

    while let Some(largest) = pq.pop() {
        if largest.score < eps_2 || boundary_nodes.len() >= max_len {
            break;
        }

        // Regularity check
        let coprime_node = BoundaryNode(largest.edge.opposite_vertex().unwrap());
        if boundary_nodes.contains(&coprime_node) {
            continue;
        }

        if largest.edge.is_constraint_edge() {
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
    edge: DirectedEdgeHandle<'a, Point2<T>, (), CdtEdge<()>, ()>,
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
