use crate::extensions::ord_triangles::OrdTriangle;

use geo::algorithm::{Area, Intersects};
use geo::geometry::{Coord, Line, LineString, Point};
use geo::{CoordFloat, GeoFloat, Polygon};

use rayon::prelude::*;

use rstar::primitives::CachedEnvelope;
use rstar::{RTree, RTreeNum, RTreeObject};

use crate::algorithms::line_intersect::LineInterval;
use crate::extensions::segments::{FromSegments, HullSegments};
use std::cmp::Ordering;
use std::collections::BinaryHeap;

#[derive(Debug)]
struct VWEdge<T: CoordFloat> {
    score: T,
    new: Coord<T>,
    ll: usize,
    left: usize,
    right: usize,
    rr: usize,
}

// These impls give us a min-heap
impl<T: CoordFloat> Ord for VWEdge<T> {
    fn cmp(&self, other: &VWEdge<T>) -> Ordering {
        other.score.partial_cmp(&self.score).unwrap()
    }
}

impl<T: CoordFloat> PartialOrd for VWEdge<T> {
    fn partial_cmp(&self, other: &VWEdge<T>) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<T> Eq for VWEdge<T> where T: CoordFloat {}

impl<T: CoordFloat> PartialEq for VWEdge<T> {
    fn eq(&self, other: &VWEdge<T>) -> bool {
        self.score == other.score
    }
}

fn visvalingam_convex<T>(mut orig: LineString<T>, eps: T) -> Vec<Coord<T>>
where
    T: GeoFloat + RTreeNum,
{
    if orig.0.len() < 3 || eps <= T::zero() {
        return orig.0.to_vec();
    }

    let max = orig.0.len();

    let tree: RTree<CachedEnvelope<_>> =
        RTree::bulk_load(orig.lines().map(CachedEnvelope::new).collect::<Vec<_>>());

    let mut adjacent: Vec<_> = (0..max)
        .map(|i| {
            if i == 0 {
                (-1_i32, 1_i32)
            } else {
                ((i - 1) as i32, (i + 1) as i32)
            }
        })
        .collect();

    let mut pq = orig
        .lines()
        .collect::<Vec<_>>()
        .windows(3)
        .enumerate()
        .filter_map(|(i, w)| {
            let &[left, _, right] = w else { unreachable!() };

            let left_ray = LineInterval::ray(left);
            let right_ray = LineInterval::ray(Line::new(right.end, right.start));
            let new: Coord<T> = left_ray.relate(&right_ray).unique_intersection()?.into();

            let score = OrdTriangle(left.end, new, right.start).signed_area();
            Some(VWEdge {
                score,
                new,
                ll: i,
                left: i + 1,
                right: i + 2,
                rr: i + 3,
            })
        })
        .filter(|e| e.score >= T::zero())
        .collect::<BinaryHeap<VWEdge<_>>>();

    while let Some(smallest) = pq.pop() {
        if smallest.score > eps {
            break;
        }

        let (ll, right) = adjacent[smallest.left];
        if ll != smallest.ll as i32 || right != smallest.right as i32 {
            continue;
        }
        let (left, rr) = adjacent[smallest.right];
        if left != smallest.left as i32 || rr != smallest.rr as i32 {
            continue;
        }

        // if tree_intersect(&tree, &smallest, &orig.0) {
        //     continue;
        // }

        // Update left coordinate
        orig.0[left as usize] = smallest.new;

        // Drop right coordinate and update adjacency
        let (lll, _) = adjacent[ll as usize];
        let (_, rrr) = adjacent[rr as usize];
        adjacent[left as usize] = (ll, rr);
        adjacent[rr as usize] = (left, rrr);
        adjacent[smallest.right] = (0, 0);

        recompute_edges(&orig, &mut pq, lll, ll, left, rr, rrr, max);
    }

    orig.0
        .iter()
        .zip(adjacent.iter())
        .filter_map(|(tup, adj)| if *adj != (0, 0) { Some(*tup) } else { None })
        .collect()
}

fn tree_intersect<T>(
    tree: &RTree<CachedEnvelope<Line<T>>>,
    triangle: &VWEdge<T>,
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

fn recompute_edges<T: GeoFloat>(
    orig: &LineString<T>,
    pq: &mut BinaryHeap<VWEdge<T>>,
    lll: i32,
    ll: i32,
    left: i32,
    rr: i32,
    rrr: i32,
    max: usize,
) {
    let choices = [(lll, ll, left, rr), (ll, left, rr, rrr)];
    for &(ai, bi, ci, di) in &choices {
        if ai as usize >= max || di as usize >= max {
            continue;
        }

        let left_ray = LineInterval::ray(Line::new(orig.0[ai as usize], orig.0[bi as usize]));
        let right_ray = LineInterval::ray(Line::new(orig.0[di as usize], orig.0[ci as usize]));

        let new: Coord<T> = match left_ray.relate(&right_ray).unique_intersection() {
            Some(new_point) => new_point.into(),
            None => continue,
        };

        let area = OrdTriangle::new(orig.0[bi as usize], new, orig.0[ci as usize]).signed_area();

        if area < T::zero() {
            continue;
        }

        let e = VWEdge {
            score: area,
            new,
            ll: ai as usize,
            left: bi as usize,
            right: ci as usize,
            rr: di as usize,
        };
        pq.push(e);
    }
}

pub trait SimplifyVWConvex<T, Epsilon = T> {
    fn simplify_vw_convex(self, eps: Epsilon) -> Self;
}

impl<T> SimplifyVWConvex<T> for LineString<T>
where
    T: GeoFloat + RTreeNum,
{
    fn simplify_vw_convex(self, eps: T) -> Self {
        LineString::from(visvalingam_convex(self, eps))
    }
}

impl<T> SimplifyVWConvex<T> for Polygon<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_vw_convex(self, eps: T) -> Self {
        let reduced_segments = self
            .hull_segments()
            .into_par_iter()
            .map(|ls| ls.simplify_vw_convex(eps))
            .collect::<Vec<_>>();

        Polygon::from_segments(reduced_segments)
    }
}
