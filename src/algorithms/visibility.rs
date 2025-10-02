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

use geo::{coord, Coord, GeoFloat, GeoNum, Kernel, Orientation};
use std::ops::Sub;

fn left_visibility_polygon<T: GeoNum>(
    mut points_iter: impl Iterator<Item = (usize, Coord<T>)>,
) -> Vec<(usize, Coord<T>)> {
    let first: (usize, Coord<T>) = points_iter.next().unwrap();
    let second = points_iter.next().unwrap();
    let mut stack = Vec::from([first, second]);

    while let Some(v) = points_iter.next() {
        if let Some(v) = if matches!(
            T::Ker::orient2d(first.1, stack.last().unwrap().1, v.1),
            Orientation::CounterClockwise
        ) {
            // Line extends visible region
            Some(v)
        } else if matches!(
            T::Ker::orient2d(
                stack.get(stack.len().sub(2)).unwrap().1,
                stack.last().unwrap().1,
                v.1
            ),
            Orientation::CounterClockwise
        ) {
            // Line lies inside the visible region (blocking)
            reduce(v, first, &mut stack) // Drop all shadowed points
        } else {
            // Line lies outside the visible region (shadowed)
            skip(first, *stack.last().unwrap(), &mut points_iter) // Iterate until visible
        } {
            stack.push(v);
        }
    }
    stack
}

fn reduce<T: GeoNum>(
    v: (usize, Coord<T>),
    first: (usize, Coord<T>),
    stack: &mut Vec<(usize, Coord<T>)>,
) -> Option<(usize, Coord<T>)> {
    let x = stack.pop().unwrap();
    while matches!(
        T::Ker::orient2d(first.1, v.1, stack.last().unwrap().1),
        Orientation::CounterClockwise
    ) && matches!(
        T::Ker::orient2d(x.1, v.1, stack.last().unwrap().1),
        Orientation::CounterClockwise
    ) {
        stack.pop();
    }

    if matches!(
        T::Ker::orient2d(first.1, stack.last().unwrap().1, v.1),
        Orientation::CounterClockwise
    ) {
        Some(v)
    } else {
        None
    }
}

fn skip<T: GeoNum>(
    first: (usize, Coord<T>),
    last: (usize, Coord<T>),
    points_iter: &mut impl Iterator<Item = (usize, Coord<T>)>,
) -> Option<(usize, Coord<T>)> {
    points_iter.find(|&v| {
        matches!(
            T::Ker::orient2d(first.1, last.1, v.1),
            Orientation::CounterClockwise
        )
    })
}

fn merge_walk<S, T>(x: Vec<(S, T)>, y: Vec<(S, T)>) -> Vec<(S, T)>
where
    S: PartialOrd + PartialEq,
{
    let x_iter = x.into_iter();
    let mut y_iter = y.into_iter();

    let mut intersection = Vec::new();
    let Some(mut other) = y_iter.next() else {
        return intersection;
    };

    for item in x_iter {
        while item.0 > other.0 {
            other = match y_iter.next() {
                Some(other) => other,
                None => return intersection,
            };
        }
        if item.0 == other.0 {
            intersection.push(item);
        }
    }
    intersection
}

fn reverse_coords<T: GeoFloat>(
    ls: impl DoubleEndedIterator<Item = (usize, Coord<T>)>,
) -> impl Iterator<Item = (usize, Coord<T>)> {
    ls.into_iter().rev().map(|v| {
        let (x, y) = v.1.x_y();
        (v.0, coord! {x: -x, y: y})
    })
}

pub fn visiblity_polygon<T: GeoFloat>(ls: &[Coord<T>]) -> Vec<(usize, Coord<T>)> {
    let iter = ls.iter().copied().enumerate();
    let left = left_visibility_polygon(iter);

    let rev_iter = reverse_coords(ls.iter().copied().enumerate());
    let rev_right = left_visibility_polygon(rev_iter);
    let right = reverse_coords(rev_right.into_iter()).collect::<Vec<_>>();
    merge_walk(left, right)
}

#[cfg(test)]
mod tests {
    use super::visiblity_polygon;
    use geo::coord;

    #[test]
    fn visibility_test() {
        let ls = vec![
            coord! { x: 0.0, y: 0.0 },
            coord! { x: 0.0, y: -1.0 },
            coord! { x: -2.0, y: -1.0 },
            coord! { x: -2.0, y: -3.0 },
            coord! { x: 2.0, y: -3.0 },
            coord! { x: 2.0, y: -2.0 },
            coord! { x: -1.0, y: -2.0 },
            coord! { x: 2.0, y: -1.0 },
            coord! { x: 2.0, y: 0.0 },
        ];
        let correct = vec![
            (0, coord! { x: 0.0, y: 0.0 }),
            (1, coord! { x: 0.0, y: -1.0 }),
            (7, coord! { x: 2.0, y: -1.0 }),
            (8, coord! { x: 2.0, y: 0.0 }),
        ];
        assert_eq!(visiblity_polygon(&ls), correct);
    }

    #[test]
    fn collinear_test() {
        let ls = vec![
            coord! { x: 0.0, y: 0.0 },
            coord! { x: 1.0, y: -2.0 },
            coord! { x: 2.0, y: 0.0 },
            coord! { x: 3.0, y: 0.0 },
            coord! { x: 4.0, y: -2.0 },
            coord! { x: 5.0, y: 0.0 },
        ];
        let correct = vec![
            (0, coord! { x: 0.0, y: 0.0 }),
            (2, coord! { x: 2.0, y: 0.0 }),
            (3, coord! { x: 3.0, y: 0.0 }),
            (5, coord! { x: 5.0, y: 0.0 }),
        ];
        assert_eq!(visiblity_polygon(&ls), correct);
    }
}
