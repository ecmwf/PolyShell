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
use spade::handles::DirectedEdgeHandle;
use spade::{CdtEdge, Point2, SpadeNum};

/// Take a given window (left, right) on an edge e and recurse on the visible edges
fn visit_edge<'a, T>(
    source: Point2<T>,
    edge: DirectedEdgeHandle<'a, Point2<T>, (), CdtEdge<()>, ()>,
    left: Point2<T>,
    right: Point2<T>,
) where
    T: GeoNum + SpadeNum,
{
    for edge in [edge.prev(), edge.next()] {
        let from = edge.from().index();
        let to = edge.to().index();

        if from == to + 1 || to == from + 1 {
            // Edge lies on the boundary, and thus blocks vision
            println!("Found edge {:?}", edge.positions());
            continue;
        }

        // Update horizons
        let new_left = if matches!(
            orient2d(source, left, edge.to().position()),
            Orientation::CounterClockwise,
        ) {
            // Vision is restricte dy the new edge
            edge.to().position()
        } else {
            // TODO: left may still need to be updated
            left
        };
        let new_right = if matches!(
            orient2d(source, right, edge.from().position()),
            Orientation::Clockwise,
        ) {
            // Vision is restricted by the new edge
            edge.from().position()
        } else {
            // TODO: right may still need to be updated
            right
        };

        if matches!(orient2d(source, left, right), Orientation::Clockwise,) {
            visit_edge(source, edge.rev(), new_left, new_right)
        }
    }
}

fn orient2d<T: GeoNum>(x: Point2<T>, y: Point2<T>, z: Point2<T>) -> Orientation {
    let points = [x, y, z];
    let [x, y, z] = points.map(|p| Coord { x: p.x, y: p.y });
    T::Ker::orient2d(x, y, z)
}

pub fn visibility_polygon<T: GeoNum>(ls: &[Coord<T>]) -> Vec<(usize, Coord<T>)> {
    vec![]
}

#[cfg(test)]
mod test {
    use geo::{polygon, CoordsIter};
    use spade::{ConstrainedDelaunayTriangulation, Point2, Triangulation};

    use crate::algorithms::visibility::visit_edge;

    #[test]
    fn snail_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 0.0, y: -2.0),
            (x: -2.0, y: -2.0),
            (x: -2.0, y: -1.0),
            (x: -1.0, y: -1.0),
            (x: -3.0, y: 0.0),
            (x: -3.0, y: -3.0),
            (x: 0.0, y: -3.0),
            (x: 3.0, y: -3.0),
            (x: 3.0, y: 0.0),
        ];
        let vertices = poly
            .exterior_coords_iter()
            .take(poly.exterior().0.len() - 1) // duplicate points are removed
            .map(|c| Point2::new(c.x, c.y))
            .collect::<Vec<_>>();

        let edges = (0..poly.exterior().0.len() - 2)
            .map(|i| {
                if i == 0 {
                    [vertices.len() - 1, i]
                } else {
                    [i, i + 1]
                }
            })
            .collect::<Vec<_>>();

        let cdt =
            ConstrainedDelaunayTriangulation::<Point2<_>>::bulk_load_cdt(vertices, edges).unwrap();

        // Pick any point
        let source = Point2::new(1.0, 1.0);

        // Get any starting edge
        let edge = cdt.vertices().next().unwrap().out_edge().unwrap();
        println!("Initial edge: {:?}", edge.positions());

        visit_edge(source, edge, edge.from().position(), edge.to().position());

        panic!();
    }
}
