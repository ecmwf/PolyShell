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

use crate::algorithms::visibility::visibility_intersection;
use crate::extensions::conversions::IntoCoord;
use crate::extensions::segments::FromSegments;
use crate::extensions::triangulate::Triangulate;
use geo::{Distance, Euclidean, GeoFloat, Line, LineString, Polygon};
use spade::handles::{FixedVertexHandle, VertexHandle};
use spade::{CdtEdge, ConstrainedDelaunayTriangulation, Point2, SpadeNum, Triangulation};

struct CircularIterator<'a, T: SpadeNum> {
    current: VertexHandle<'a, Point2<T>, (), CdtEdge<()>>,
    until: VertexHandle<'a, Point2<T>, (), CdtEdge<()>>,
    cdt: &'a ConstrainedDelaunayTriangulation<Point2<T>>,
}

impl<'a, T: SpadeNum> CircularIterator<'a, T> {
    fn new(
        from: VertexHandle<'a, Point2<T>, (), CdtEdge<()>>,
        until: VertexHandle<'a, Point2<T>, (), CdtEdge<()>>,
        cdt: &'a ConstrainedDelaunayTriangulation<Point2<T>>,
    ) -> Self {
        CircularIterator {
            current: from,
            until,
            cdt,
        }
    }
}

impl<'a, T: SpadeNum> Iterator for CircularIterator<'a, T> {
    type Item = VertexHandle<'a, Point2<T>, (), CdtEdge<()>>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.current == self.until {
            return None;
        }

        let vertex = self.current;

        self.current = {
            let handle =
                FixedVertexHandle::from_index((self.current.index() + 1) % self.cdt.num_vertices());
            self.cdt.get_vertex(handle).unwrap()
        };

        Some(vertex)
    }
}

fn rdp_preserve<T>(
    from: VertexHandle<'_, Point2<T>, (), CdtEdge<()>>,
    to: VertexHandle<'_, Point2<T>, (), CdtEdge<()>>,
    cdt: &ConstrainedDelaunayTriangulation<Point2<T>>,
    eps: T,
) -> Vec<Point2<T>>
where
    T: SpadeNum + GeoFloat + Send + Sync,
{
    if cdt.exists_constraint(from.fix(), to.fix()) {
        return vec![from.position(), to.position()];
    }

    let chord = {
        let [from, to] = [from, to].map(|v| v.position().into_coord());
        Line::new(from, to)
    };

    let farthest_distance =
        CircularIterator::new(from, to, cdt).fold(T::zero(), |farthest_distance, v| {
            let distance = Euclidean.distance(v.position().into_coord(), &chord);
            if distance > farthest_distance {
                distance
            } else {
                farthest_distance
            }
        });

    if farthest_distance <= eps {
        return vec![from.position(), to.position()];
    }

    let (split_vertex, _) = visibility_intersection(from, to, cdt).into_iter().fold(
        (from, -T::one()), // Placeholder, should always be overwritten
        |(farthest_vertex, farthest_distance), v| {
            let distance = Euclidean.distance(v.position().into_coord(), &chord);
            if distance > farthest_distance {
                (v, distance)
            } else {
                (farthest_vertex, farthest_distance)
            }
        },
    );

    // This should never occur
    if split_vertex == from || split_vertex == to {
        panic!("Attempted to split at endpoint");
    }

    let (mut left, right) = rayon::join(
        || rdp_preserve(from, split_vertex, cdt, eps),
        || rdp_preserve(split_vertex, to, cdt, eps),
    );

    left.pop();
    left.extend_from_slice(&right);

    left
}

pub trait SimplifyRDP<T, Epsilon = T> {
    fn simplify_rdp(&self, eps: Epsilon) -> Self;
}

impl<T> SimplifyRDP<T> for Polygon<T>
where
    T: SpadeNum + GeoFloat + Send + Sync,
{
    fn simplify_rdp(&self, eps: T) -> Self {
        let cdt = self.triangulate();

        let segments = cdt
            .convex_hull()
            .map(|edge| {
                rdp_preserve(edge.from(), edge.to(), &cdt, eps)
                    .into_iter()
                    .map(|point| point.into_coord())
                    .collect::<LineString<_>>()
            })
            .collect();

        Polygon::from_segments(segments)
    }
}
