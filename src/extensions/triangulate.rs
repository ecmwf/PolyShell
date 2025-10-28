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

use geo::{CoordsIter, GeoNum, Polygon};
use spade::{ConstrainedDelaunayTriangulation, Point2, SpadeNum};

pub trait Triangulate<T: SpadeNum> {
    fn triangulate(&self) -> ConstrainedDelaunayTriangulation<Point2<T>>;
}

impl<T> Triangulate<T> for Polygon<T>
where
    T: SpadeNum + GeoNum,
{
    fn triangulate(&self) -> ConstrainedDelaunayTriangulation<Point2<T>> {
        let num_vertices = self.exterior().0.len() - 1;

        let vertices = self
            .exterior_coords_iter()
            .take(num_vertices) // duplicate points are removed
            .map(|c| Point2::new(c.x, c.y))
            .collect();

        let edges = (0..num_vertices)
            .map(|i| {
                if i == 0 {
                    [num_vertices - 1, 0]
                } else {
                    [i - 1, i]
                }
            })
            .collect();

        ConstrainedDelaunayTriangulation::<Point2<T>>::bulk_load_cdt(vertices, edges).unwrap()
    }
}
