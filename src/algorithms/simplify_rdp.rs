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

use crate::algorithms::visibility::visiblity_polygon;
use crate::extensions::segments::{FromSegments, HullSegments};
use geo::{Coord, Distance, Euclidean, GeoFloat, Line, LineString, Polygon};
use rayon::prelude::*;

fn rdp_preserve<T>(ls: &[Coord<T>], eps: T) -> Vec<Coord<T>>
where
    T: GeoFloat + Send + Sync,
{
    let (first, last) = match ls {
        [] => return vec![],
        &[only] => return vec![only],
        &[first, last] => return vec![first, last],
        &[first, .., last] => (first, last),
    };

    let visible = visiblity_polygon(ls);
    let chord = Line::new(first, last);

    let split_index = visible
        .into_iter()
        .skip(1)
        .fold(
            (0usize, T::zero()),
            |(farthest_index, farthest_distance), (index, coord)| {
                let distance = Euclidean.distance(coord, &chord);
                if distance < farthest_distance {
                    (farthest_index, farthest_distance)
                } else {
                    (index, distance)
                }
            },
        )
        .0;

    if split_index == 0 || split_index == ls.len() - 1 {
        println!("Failed to reduce. Skipping.");
        return vec![first, last];
    }

    let farthest_distance = ls.iter().map(|&v| Euclidean.distance(v, &chord)).fold(
        T::zero(),
        |farthest_distance, distance| {
            if distance > farthest_distance {
                distance
            } else {
                farthest_distance
            }
        },
    );

    if farthest_distance > eps {
        let (mut left, right) = rayon::join(
            || rdp_preserve(&ls[..=split_index], eps),
            || rdp_preserve(&ls[split_index..], eps),
        );

        left.pop();
        left.extend_from_slice(&right);

        return left;
    }

    vec![first, last]
}

pub trait SimplifyRDP<T, Epsilon = T> {
    fn simplify_rdp(&self, eps: Epsilon) -> Self;
}

impl<T> SimplifyRDP<T> for LineString<T>
where
    T: GeoFloat + Send + Sync,
{
    fn simplify_rdp(&self, eps: T) -> Self {
        LineString::new(rdp_preserve(&self.0, eps))
    }
}

impl<T> SimplifyRDP<T> for Polygon<T>
where
    T: GeoFloat + Send + Sync,
{
    fn simplify_rdp(&self, eps: T) -> Self {
        let reduced_segments = self
            .hull_segments()
            .into_par_iter() // parallelize with rayon
            .map(|ls| ls.simplify_rdp(eps))
            .collect::<Vec<_>>();

        Polygon::from_segments(reduced_segments)
    }
}
