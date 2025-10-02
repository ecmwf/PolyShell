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

use crate::algorithms::hull_melkman::Melkman;
use geo::{GeoNum, LineString, Polygon};

pub trait HullSegments<T: GeoNum> {
    fn hull_segments(&self) -> Vec<LineString<T>>;
}

impl<T: GeoNum> HullSegments<T> for Polygon<T> {
    fn hull_segments(&self) -> Vec<LineString<T>> {
        let coord_vec = &self.exterior().0;
        self.hull_indices()
            .windows(2)
            .map(|window| {
                let &[start, end] = window else {
                    unreachable!()
                };
                if start <= end {
                    LineString::new(coord_vec[start..=end].to_vec())
                } else {
                    LineString::new([&coord_vec[start..], &coord_vec[1..=end]].concat())
                }
            })
            .collect::<Vec<_>>()
    }
}

pub trait FromSegments<T> {
    fn from_segments(segments: T) -> Self;
}

impl<T: GeoNum> FromSegments<Vec<LineString<T>>> for LineString<T> {
    fn from_segments(segments: Vec<LineString<T>>) -> Self {
        segments
            .into_iter()
            .map(|ls| ls.into_inner())
            .reduce(|mut acc, new| {
                acc.extend(new.into_iter().skip(1));
                acc
            })
            .unwrap_or_default()
            .into()
    }
}

impl<T: GeoNum> FromSegments<Vec<LineString<T>>> for Polygon<T> {
    fn from_segments(segments: Vec<LineString<T>>) -> Self {
        Polygon::new(LineString::from_segments(segments), vec![])
    }
}
