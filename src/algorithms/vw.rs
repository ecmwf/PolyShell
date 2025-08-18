use crate::extensions::ord_triangles::{OrdTriangle, OrdTriangles};

use geo::algorithm::{Area, Intersects};
use geo::geometry::{Coord, Line, LineString, Point, Polygon};
use geo::{CoordFloat, GeoFloat};

use rayon::prelude::*;

use rstar::primitives::CachedEnvelope;
use rstar::{RTree, RTreeNum, RTreeObject};

use crate::extensions::segments::{FromSegments, HullSegments};
use std::cmp::Ordering;
use std::collections::BinaryHeap;

#[derive(Debug)]
struct VWScore<T: CoordFloat> {
    score: T,
    current: usize,
    left: usize,
    right: usize,
}

// These impls give us a min-heap
impl<T: CoordFloat> Ord for VWScore<T> {
    fn cmp(&self, other: &VWScore<T>) -> Ordering {
        other.score.partial_cmp(&self.score).unwrap()
    }
}

impl<T: CoordFloat> PartialOrd for VWScore<T> {
    fn partial_cmp(&self, other: &VWScore<T>) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<T> Eq for VWScore<T> where T: CoordFloat {}

impl<T: CoordFloat> PartialEq for VWScore<T> {
    fn eq(&self, other: &VWScore<T>) -> bool {
        self.score == other.score
    }
}

fn visvalingam_preserve<T>(orig: &LineString<T>, epsilon: T) -> Vec<Coord<T>>
where
    T: GeoFloat + RTreeNum,
{
    if orig.0.len() < 3 || epsilon <= T::zero() {
        return orig.0.to_vec();
    }

    let max = orig.0.len();

    let tree: RTree<CachedEnvelope<_>> =
        RTree::bulk_load(orig.lines().map(CachedEnvelope::new).collect::<Vec<_>>());

    let mut adjacent: Vec<_> = (0..orig.0.len())
        .map(|i| {
            if i == 0 {
                (-1_i32, 1_i32)
            } else {
                ((i - 1) as i32, (i + 1) as i32)
            }
        })
        .collect();

    let mut pq = orig
        .ord_triangles()
        .enumerate()
        .map(|(i, triangle)| VWScore {
            score: triangle.signed_area(),
            current: i + 1,
            left: i,
            right: i + 2,
        })
        .filter(|point| point.score >= T::zero())
        .collect::<BinaryHeap<VWScore<T>>>();

    while let Some(smallest) = pq.pop() {
        if smallest.score > epsilon {
            break;
        }

        let (left, right) = adjacent[smallest.current];
        if left != smallest.left as i32 || right != smallest.right as i32 {
            continue;
        }

        if tree_intersect(&tree, &smallest, &orig.0) {
            continue;
        }

        let (ll, _) = adjacent[left as usize];
        let (_, rr) = adjacent[right as usize];
        adjacent[left as usize] = (ll, right);
        adjacent[right as usize] = (left, rr);
        adjacent[smallest.current] = (0, 0);

        recompute_triangles(orig, &mut pq, ll, left, right, rr, max);
    }

    orig.0
        .iter()
        .zip(adjacent.iter())
        .filter_map(|(tup, adj)| if *adj != (0, 0) { Some(*tup) } else { None })
        .collect()
}

fn tree_intersect<T>(
    tree: &RTree<CachedEnvelope<Line<T>>>,
    triangle: &VWScore<T>,
    orig: &[Coord<T>],
) -> bool
where
    T: GeoFloat + RTreeNum,
{
    let new_segment_start = orig[triangle.left];
    let new_segment_end = orig[triangle.right];

    let new_segment = CachedEnvelope::new(Line::new(
        Point::from(new_segment_start),
        Point::from(new_segment_end),
    ));

    let bounding_rect = new_segment.envelope();

    tree.locate_in_envelope_intersecting(&bounding_rect)
        .any(|candidate| {
            let (candidate_start, candidate_end) = candidate.points();
            candidate_start.0 != new_segment_start
                && candidate_start.0 != new_segment_end
                && candidate_end.0 != new_segment_start
                && candidate_end.0 != new_segment_end
                && new_segment.intersects(&**candidate)
        })
}

fn recompute_triangles<T: CoordFloat>(
    orig: &LineString<T>,
    pq: &mut BinaryHeap<VWScore<T>>,
    ll: i32,
    left: i32,
    right: i32,
    rr: i32,
    max: usize,
) {
    let choices = [(ll, left, right), (left, right, rr)];
    for &(ai, current_point, bi) in &choices {
        if ai as usize >= max || bi as usize >= max {
            continue;
        }

        let area = OrdTriangle::new(
            orig.0[ai as usize],
            orig.0[current_point as usize],
            orig.0[bi as usize],
        )
        .signed_area();

        if area < T::zero() {
            continue;
        }

        let v = VWScore {
            score: area,
            current: current_point as usize,
            left: ai as usize,
            right: bi as usize,
        };
        pq.push(v);
    }
}

pub trait SimplifyVW<T, Epsilon = T> {
    fn simplify_vw(&self, epsilon: Epsilon) -> Self;
}

impl<T> SimplifyVW<T> for LineString<T>
where
    T: GeoFloat + RTreeNum,
{
    fn simplify_vw(&self, epsilon: T) -> Self {
        LineString::from(visvalingam_preserve(self, epsilon))
    }
}

impl<T> SimplifyVW<T> for Polygon<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_vw(&self, epsilon: T) -> Self {
        let reduced_segments = self
            .hull_segments()
            .into_par_iter() // parallelize with rayon
            .map(|ls| ls.simplify_vw(epsilon))
            .collect::<Vec<_>>();

        Polygon::from_segments(reduced_segments)
    }
}
