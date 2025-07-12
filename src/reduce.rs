use crate::convex_hull::melkman_indices;
use geo::{
    Area, BoundingRect, Coord, CoordFloat, GeoFloat, Intersects, Line, LineString, Point, Polygon,
    Triangle,
};
use rstar::primitives::CachedEnvelope;
use rstar::{RTree, RTreeNum};
use std::cmp::Ordering;
use std::collections::BinaryHeap;

use rayon::prelude::*;

#[derive(Debug)]
struct VScore<T>
where
    T: CoordFloat,
{
    score: T,
    current: usize,
    left: usize,
    right: usize,
}

// These impls give us a min-heap
impl<T> Ord for VScore<T>
where
    T: CoordFloat,
{
    fn cmp(&self, other: &VScore<T>) -> Ordering {
        other.score.partial_cmp(&self.score).unwrap()
    }
}

impl<T> PartialOrd for VScore<T>
where
    T: CoordFloat,
{
    fn partial_cmp(&self, other: &VScore<T>) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<T> Eq for VScore<T> where T: CoordFloat {}

impl<T> PartialEq for VScore<T>
where
    T: CoordFloat,
{
    fn eq(&self, other: &VScore<T>) -> bool
    where
        T: CoordFloat,
    {
        self.score == other.score
    }
}

pub fn linestring_to_points<T>(linestring: &LineString<T>) -> Vec<[T; 2]>
where
    T: CoordFloat,
{
    linestring.coords().map(|c| [c.x, c.y]).collect()
}

pub fn polygon_to_points<T>(polygon: &Polygon<T>) -> Vec<[T; 2]>
where
    T: CoordFloat,
{
    linestring_to_points(polygon.exterior())
}

fn visvalingam_preserve<T>(orig: &LineString<T>, epsilon: T) -> Vec<Coord<T>>
where
    T: GeoFloat + RTreeNum,
{
    if orig.0.len() < 3 || epsilon <= T::zero() {
        return orig.0.to_vec();
    }

    let max = orig.0.len();

    let mut tree: RTree<CachedEnvelope<_>> =
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
        .triangles()
        .enumerate()
        .map(|(i, triangle)| VScore {
            score: triangle.signed_area(),
            current: i + 1,
            left: i,
            right: i + 2,
        })
        .filter(|point| point.score >= T::zero())
        .collect::<BinaryHeap<VScore<T>>>();

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

        let left_point = Coord::from(orig.0[left as usize]);
        let right_point = Coord::from(orig.0[right as usize]);
        tree.insert(CachedEnvelope::new(Line::new(left_point, right_point)));

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
    triangle: &VScore<T>,
    orig: &[Coord<T>],
) -> bool
where
    T: GeoFloat + RTreeNum,
{
    let new_segment_start = orig[triangle.left];
    let new_segment_end = orig[triangle.right];

    let new_segment = CachedEnvelope::new(Line::new(
        Point::from(orig[triangle.left]),
        Point::from(orig[triangle.right]),
    ));

    let bounding_rect = Triangle::new(
        orig[triangle.left],
        orig[triangle.current],
        orig[triangle.right],
    )
        .bounding_rect();

    tree.locate_in_envelope_intersecting(&rstar::AABB::from_corners(
        bounding_rect.min().into(),
        bounding_rect.max().into(),
    ))
        .any(|candidate| {
            let (candidate_start, candidate_end) = candidate.points();
            candidate_start.0 != new_segment_start
                && candidate_start.0 != new_segment_end
                && candidate_end.0 != new_segment_start
                && candidate_end.0 != new_segment_end
                && (*new_segment).intersects(&**candidate)
        })
}

fn recompute_triangles<T>(
    orig: &LineString<T>,
    pq: &mut BinaryHeap<VScore<T>>,
    ll: i32,
    left: i32,
    right: i32,
    rr: i32,
    max: usize,
) where
    T: CoordFloat,
{
    let choices = [(ll, left, right), (left, right, rr)];
    for &(ai, current_point, bi) in &choices {
        if ai as usize >= max || bi as usize >= max {
            continue;
        }

        let area = Triangle::new(
            orig.0[ai as usize],
            orig.0[current_point as usize],
            orig.0[bi as usize],
        )
            .signed_area();

        if area < T::zero() {
            continue;
        }

        let v = VScore {
            score: area,
            current: current_point as usize,
            left: ai as usize,
            right: bi as usize,
        };
        pq.push(v);
    }
}

pub trait SimplifyVwPreserve<T, Epsilon = T> {
    fn simplify_vw_preserve(&self, epsilon: T) -> Self
    where
        T: GeoFloat + RTreeNum;
}

impl<T> SimplifyVwPreserve<T> for LineString<T>
where
    T: GeoFloat + RTreeNum,
{
    fn simplify_vw_preserve(&self, epsilon: T) -> Self {
        LineString::from(visvalingam_preserve(self, epsilon))
    }
}

impl<T> SimplifyVwPreserve<T> for Polygon<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_vw_preserve(&self, epsilon: T) -> Self {
        // Divide into segments between convex hull vertices
        let hull_indices = melkman_indices(self);
        let coord_vec = &self.exterior().0;

        let segments = hull_indices
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
            .collect::<Vec<_>>();

        // Reduce line segments and merge
        let reduced_segments = segments
            .into_par_iter() // parallelize with rayon
            .map(|ls| ls.simplify_vw_preserve(epsilon))
            .collect::<Vec<_>>();

        let exterior = reduced_segments
            .into_iter()
            .map(|ls| ls.into_inner())
            .reduce(|mut acc, new| {
                acc.extend(new.into_iter().skip(1));
                acc
            })
            .unwrap();

        Polygon::new(LineString::new(exterior), vec![])
    }
}
