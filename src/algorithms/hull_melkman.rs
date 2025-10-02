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

use geo::{Coord, CoordsIter, GeoNum, Kernel, Orientation, Polygon};
use std::collections::VecDeque;
use std::ops::Sub;

trait SecondIndex<T> {
    fn front_less(&self) -> Option<&T>;
    fn back_less(&self) -> Option<&T>;
}

impl<T> SecondIndex<T> for VecDeque<T> {
    fn front_less(&self) -> Option<&T> {
        self.get(1)
    }

    fn back_less(&self) -> Option<&T> {
        self.get(self.len().sub(2))
    }
}

fn melkman<T: GeoNum>(poly: &Polygon<T>) -> Vec<(usize, Coord<T>)> {
    let [x, y] = match poly.exterior().0.as_slice() {
        [] => return vec![],
        &[x] => return vec![(0, x)],
        &[x, y, ..] => [(0, x), (1, y)],
    };

    let mut hull = VecDeque::from([y, x, y]);

    let poly_iter = poly
        .exterior_coords_iter()
        .enumerate()
        .skip(2)
        .take(poly.exterior().0.len() - 1);

    for (index, v) in poly_iter {
        if matches!(
            T::Ker::orient2d(v, hull.front().unwrap().1, hull.front_less().unwrap().1),
            Orientation::CounterClockwise | Orientation::Collinear
        ) || matches!(
            T::Ker::orient2d(v, hull.back().unwrap().1, hull.back_less().unwrap().1),
            Orientation::Clockwise | Orientation::Collinear
        ) {
            while let Orientation::CounterClockwise | Orientation::Collinear =
                T::Ker::orient2d(v, hull.front().unwrap().1, hull.front_less().unwrap().1)
            {
                hull.pop_front();
            }
            while let Orientation::Clockwise | Orientation::Collinear =
                T::Ker::orient2d(v, hull.back().unwrap().1, hull.back_less().unwrap().1)
            {
                hull.pop_back();
            }

            hull.push_front((index, v));
            hull.push_back((index, v));
        };
    }
    hull.into()
}

pub trait Melkman<T: GeoNum> {
    fn hull_indices(&self) -> Vec<usize>;
}

impl<T: GeoNum> Melkman<T> for Polygon<T> {
    fn hull_indices(&self) -> Vec<usize> {
        melkman(self).into_iter().map(|(index, _)| index).collect()
    }
}

#[cfg(test)]
mod test {
    use crate::algorithms::hull_melkman::Melkman;
    use geo::polygon;

    #[test]
    fn simple_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 0.0, y: 1.0),
            (x: 0.5, y: 0.5),
            (x: 1.0, y: 1.0),
            (x: 1.0, y: 0.0),
        ];
        let hull = poly.hull_indices();
        let correct = vec![4, 0, 1, 3, 4];
        assert_eq!(hull, correct);
    }

    #[test]
    fn collinear_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 0.0, y: 1.0),
            (x: 0.5, y: 0.5),
            (x: 1.0, y: 0.0),
        ];
        let hull = poly.hull_indices();
        let correct = vec![3, 0, 1, 3];
        assert_eq!(hull, correct);
    }
}
