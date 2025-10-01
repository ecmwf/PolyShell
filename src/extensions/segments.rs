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
            .unwrap()
            .into()
    }
}

impl<T: GeoNum> FromSegments<Vec<LineString<T>>> for Polygon<T> {
    fn from_segments(segments: Vec<LineString<T>>) -> Self {
        Polygon::new(LineString::from_segments(segments), vec![])
    }
}
