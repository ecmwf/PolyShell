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

use geo::{Coord, GeoNum, Kernel, Orientation};
use spade::handles::{DirectedEdgeHandle, FixedVertexHandle, VertexHandle};
use spade::{CdtEdge, ConstrainedDelaunayTriangulation, Point2, SpadeNum, Triangulation};
use std::collections::BinaryHeap;

/// Take a given window (left, right) on an edge e and recurse on the visible edges
fn visit_edge<'a, T>(
    source: Point2<T>,
    edge: DirectedEdgeHandle<'a, Point2<T>, (), CdtEdge<()>, ()>,
    left: VertexHandle<Point2<T>, (), CdtEdge<()>, ()>,
    right: VertexHandle<Point2<T>, (), CdtEdge<()>, ()>,
    visible: &mut BinaryHeap<VertexHandle<'a, Point2<T>, (), CdtEdge<()>>>,
) where
    T: GeoNum + SpadeNum,
{
    if edge.is_constraint_edge() || edge.is_outer_edge() {
        return;
    }

    // If coprime point is visible, push to stack
    let coprime = edge.opposite_vertex().unwrap();
    // TODO: Replace with LineSideInfo
    if matches!(
        orient2d(source, left.position(), coprime.position()),
        Orientation::Clockwise | Orientation::Collinear
    ) && matches!(
        orient2d(source, right.position(), coprime.position()),
        Orientation::CounterClockwise | Orientation::Collinear
    ) {
        visible.push(coprime);
    }

    // Iterate over new edges
    for edge in [edge.prev(), edge.next()] {
        // Update horizons
        let new_left = if matches!(
            orient2d(source, left.position(), edge.to().position()),
            Orientation::CounterClockwise,
        ) {
            // Vision is restricted by the new edge
            left
        } else {
            edge.to()
        };

        let new_right = if matches!(
            orient2d(source, right.position(), edge.from().position()),
            Orientation::Clockwise,
        ) {
            // Vision is restricted by the new edge
            right
        } else {
            edge.from()
        };

        if matches!(
            orient2d(source, new_left.position(), new_right.position()),
            Orientation::CounterClockwise
        ) {
            // Left and right have changed side: this edge is not visible
            continue;
        }

        visit_edge(source, edge.rev(), new_left, new_right, visible);
    }
}

fn orient2d<T: GeoNum>(x: Point2<T>, y: Point2<T>, z: Point2<T>) -> Orientation {
    let points = [x, y, z];
    let [x, y, z] = points.map(|p| Coord { x: p.x, y: p.y });
    T::Ker::orient2d(x, y, z)
}

fn visibility_vertex<T: GeoNum + SpadeNum>(
    mut edge: DirectedEdgeHandle<Point2<T>, (), CdtEdge<()>, ()>,
    direction: Orientation,
) -> BinaryHeap<VertexHandle<Point2<T>, (), CdtEdge<()>, ()>> {
    let mut visible = BinaryHeap::from([edge.from(), edge.to()]);
    let source = edge.from().position();

    if edge.is_outer_edge() && edge.is_constraint_edge() {
        // There are no faces to iterate over
        return visible;
    }

    if matches!(direction, Orientation::Clockwise) {
        edge = edge.rev();
    }

    while let Some(coprime) = edge.opposite_vertex() {
        visible.push(coprime);

        let window = match direction {
            Orientation::CounterClockwise => edge.next().rev(),
            Orientation::Clockwise => edge.prev().rev(),
            Orientation::Collinear => panic!(),
        };
        visit_edge(source, window, window.from(), window.to(), &mut visible);

        // Advance to next edge
        edge = match direction {
            Orientation::CounterClockwise => edge.prev().rev(),
            Orientation::Clockwise => edge.next().rev(),
            Orientation::Collinear => panic!(),
        };

        if edge.is_constraint_edge() {
            break;
        }
    }
    visible
}

pub fn visibility_intersection<'a, T: GeoNum + SpadeNum>(
    from: VertexHandle<Point2<T>, (), CdtEdge<()>>,
    to: VertexHandle<Point2<T>, (), CdtEdge<()>>,
    cdt: &'a ConstrainedDelaunayTriangulation<Point2<T>>,
) -> Vec<VertexHandle<'a, Point2<T>, (), CdtEdge<()>>> {
    let from_edge = {
        let next = FixedVertexHandle::from_index((from.index() + 1) % cdt.num_vertices());
        cdt.get_edge_from_neighbors(from.fix(), next).unwrap()
    };
    let to_edge = {
        let index = if to.index() == 0 {
            cdt.num_vertices() - 1
        } else {
            to.index() - 1
        };
        let prev = FixedVertexHandle::from_index(index);
        cdt.get_edge_from_neighbors(to.fix(), prev).unwrap()
    };

    let from_vis = visibility_vertex(from_edge, Orientation::CounterClockwise);
    let to_vis = visibility_vertex(to_edge, Orientation::Clockwise);

    binary_heap_intersection(from_vis, to_vis)
        .into_sorted_vec()
        .into_iter()
        .filter(|v| {
            if from.index() <= to.index() {
                v.index() >= from.index() && v.index() <= to.index()
            } else {
                v.index() <= to.index() || v.index() >= from.index()
            }
        })
        .collect()
}

fn binary_heap_intersection<T: Ord>(mut x: BinaryHeap<T>, mut y: BinaryHeap<T>) -> BinaryHeap<T> {
    let mut intersection = BinaryHeap::new();
    let Some(mut other) = y.pop() else {
        return intersection;
    };

    while let Some(item) = x.pop() {
        while item < other {
            other = match y.pop() {
                Some(other) => other,
                None => return intersection,
            };
        }
        if item == other {
            intersection.push(item);
        }
    }
    intersection
}

#[cfg(test)]
mod test {
    use crate::algorithms::visibility::{visibility_intersection, visit_edge};
    use crate::extensions::triangulate::Triangulate;
    use geo::polygon;
    use spade::handles::FixedVertexHandle;
    use spade::{Point2, Triangulation};
    use std::collections::BinaryHeap;

    #[test]
    fn collinear_test() {
        let poly = polygon![
            (x: 0.0, y: 1.0),
            (x: 1.0, y: 1.0),
            (x: 1.0, y: 0.0),
            (x: 0.0, y: 0.0),
        ];

        let cdt = poly.triangulate();

        let from = {
            let handle = FixedVertexHandle::from_index(0);
            cdt.get_vertex(handle).unwrap()
        };
        let to = {
            let handle = FixedVertexHandle::from_index(1);
            cdt.get_vertex(handle).unwrap()
        };

        let vis = visibility_intersection(from, to, &cdt)
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![0, 1];

        assert_eq!(vis, correct);
    }

    #[test]
    fn left_constrained_test() {}

    #[test]
    fn right_constrained_test() {}

    #[test]
    fn constrained_test() {
        let poly = polygon![
            (x: 0.0, y: 1.0),
            (x: 0.5, y: 0.5),
            (x: 1.0, y: 1.0),
            (x: 1.0, y: 0.0),
            (x: 0.0, y: 0.0),
        ];

        let cdt = poly.triangulate();

        let from = {
            let handle = FixedVertexHandle::from_index(0);
            cdt.get_vertex(handle).unwrap()
        };
        let to = {
            let handle = FixedVertexHandle::from_index(2);
            cdt.get_vertex(handle).unwrap()
        };

        let vis = visibility_intersection(from, to, &cdt)
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![0, 1, 2];

        assert_eq!(vis, correct);
    }

    #[test]
    fn central_peak_test() {
        let poly = polygon![
            (x: 0.0, y: 1.0),
            (x: 0.5, y: 0.5),
            (x: 1.0, y: 0.9),
            (x: 1.5, y: 0.5),
            (x: 2.0, y: 1.0),
            (x: 2.0, y: 0.0),
            (x: 0.0, y: 0.0),
        ];

        let cdt = poly.triangulate();

        let from = {
            let handle = FixedVertexHandle::from_index(0);
            cdt.get_vertex(handle).unwrap()
        };
        let to = {
            let handle = FixedVertexHandle::from_index(4);
            cdt.get_vertex(handle).unwrap()
        };

        let vis = visibility_intersection(from, to, &cdt)
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![0, 2, 4];

        assert_eq!(vis, correct);
    }

    #[test]
    fn sawtooth_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 1.0, y: -1.0),
            (x: 0.0, y: -2.0),
            (x: 1.0, y: -3.0),
            (x: 2.0, y: -3.0),
            (x: 1.0, y: -2.0),
            (x: 2.0, y: -1.0),
            (x: 2.0, y: 0.0),
            (x: 3.0, y: 0.0),
            (x: 3.0, y: -4.0),
            (x: -1.0, y: -4.0),
            (x: -1.0, y: 0.0),
        ];

        let cdt = poly.triangulate();

        let source = Point2::new(1.0, 1.0);
        let edge = {
            let from = FixedVertexHandle::from_index(0);
            let to = FixedVertexHandle::from_index(7);
            cdt.get_edge_from_neighbors(from, to).unwrap().rev()
        };

        let mut vis = BinaryHeap::new();
        visit_edge(source, edge, edge.from(), edge.to(), &mut vis);

        let vis = vis
            .into_sorted_vec()
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![1, 3, 5, 6];

        assert_eq!(vis, correct);
    }

    #[test]
    fn snail_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 0.0, y: -3.0),
            (x: -2.0, y: -3.0),
            (x: -2.0, y: -2.0),
            (x: -1.0, y: -2.0),
            (x: -3.0, y: -1.0),
            (x: -3.0, y: -4.0),
            (x: 3.0, y: -4.0),
            (x: 3.0, y: 0.0),
            (x: 4.0, y: 0.0),
            (x: 4.0, y: -5.0),
            (x: -4.0, y: -5.0),
            (x: -4.0, y: 0.0),
        ];

        let cdt = poly.triangulate();

        let from = {
            let handle = FixedVertexHandle::from_index(0);
            cdt.get_vertex(handle).unwrap()
        };
        let to = {
            let handle = FixedVertexHandle::from_index(8);
            cdt.get_vertex(handle).unwrap()
        };

        let vis = visibility_intersection(from, to, &cdt)
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![0, 1, 7, 8];

        assert_eq!(vis, correct);
    }

    #[test]
    fn pan_handle_test() {
        let poly = polygon![
            (x: -1.0, y: 0.0),
            (x: 0.0, y: 0.0),
            (x: 0.0, y: -1.0),
            (x: 1.0, y: -1.0),
            (x: 1.0, y: 0.0),
            (x: 2.0, y: 0.0),
            (x: 3.0, y: 1.0),
            (x: 3.0, y: -2.0),
            (x: -2.0, y: -2.0),
            (x: -2.0, y: 1.0),
        ];

        let cdt = poly.triangulate();

        let from = {
            let handle = FixedVertexHandle::from_index(0);
            cdt.get_vertex(handle).unwrap()
        };
        let to = {
            let handle = FixedVertexHandle::from_index(5);
            cdt.get_vertex(handle).unwrap()
        };

        let vis = visibility_intersection(from, to, &cdt)
            .into_iter()
            .map(|v| v.index())
            .collect::<Vec<_>>();
        let correct = vec![0, 1, 4, 5];

        assert_eq!(vis, correct);
    }
}
