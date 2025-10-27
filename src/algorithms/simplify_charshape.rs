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

use crate::extensions::conversions::IntoCoord;
use crate::extensions::triangulate::Triangulate;
use geo::{GeoFloat, Polygon};
use spade::handles::DirectedEdgeHandle;
use spade::{CdtEdge, Point2, SpadeNum, Triangulation};
use std::cmp::Ordering;
use std::collections::BinaryHeap;

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

fn characteristic_shape<T>(orig: &Polygon<T>, eps: T, max_len: usize) -> Polygon<T>
where
    T: GeoFloat + SpadeNum,
{
    if orig.exterior().0.len() < 3 {
        return orig.clone();
    }

    let eps_2 = eps * eps;

    let tri = orig.triangulate();
    let mut boundary_nodes = tri
        .convex_hull()
        .map(|edge| edge.from())
        .collect::<BinaryHeap<_>>();

    let mut pq = tri
        .convex_hull()
        .map(|edge| edge.rev())
        .map(|line| CharScore {
            score: line.length_2(),
            edge: line,
        })
        .collect::<BinaryHeap<_>>();

    while let Some(largest) = pq.pop() {
        if largest.score < eps_2 || boundary_nodes.len() >= max_len {
            break;
        }

        // Regularity check
        if largest.edge.is_constraint_edge() {
            continue;
        }

        // Update boundary nodes and edges
        let coprime_node = largest.edge.opposite_vertex().unwrap();
        boundary_nodes.push(coprime_node);
        recompute_boundary(largest.edge, &mut pq);
    }

    // Extract boundary nodes
    let exterior = boundary_nodes
        .into_sorted_vec()
        .into_iter()
        .map(|v| v.position().into_coord())
        .collect();
    Polygon::new(exterior, vec![])
}

fn recompute_boundary<'a, T>(
    edge: DirectedEdgeHandle<'a, Point2<T>, (), CdtEdge<()>, ()>,
    pq: &mut BinaryHeap<CharScore<'a, T>>,
) where
    T: GeoFloat + SpadeNum,
{
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
