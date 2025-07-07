use geo::{
    Area, BoundingRect, Coord, CoordFloat, GeoFloat, Intersects, Line, LineString, Point, Polygon,
    Triangle,
};
use rstar::primitives::CachedEnvelope;
use rstar::{RTree, RTreeNum};
use std::cmp::Ordering;
use std::collections::BinaryHeap;

use rayon::prelude::*;

use qhull::Qh;

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

trait ConvexHullIndices {
    fn convex_hull_indices(&self) -> Vec<usize>;
}

// qhull works only for f64
impl ConvexHullIndices for LineString<f64> {
    fn convex_hull_indices(&self) -> Vec<usize> {
        let qh = Qh::builder()
            .compute(true)
            .build_from_iter(linestring_to_points(self))
            .unwrap();
        
        let mut hull_indices = qh.vertices()
            .map(|v| v.index(&qh).unwrap())
            .collect::<Vec<_>>();  // qhull returns vertices unsorted
        hull_indices.sort();
    
        hull_indices
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
        let middle_point = Coord::from(orig.0[smallest.current]);
        let right_point = Coord::from(orig.0[right as usize]);

        let line_1 = CachedEnvelope::new(Line::new(left_point, middle_point));
        let line_2 = CachedEnvelope::new(Line::new(middle_point, right_point));
        assert!(tree.remove(&line_1).is_some());
        assert!(tree.remove(&line_2).is_some());

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

impl SimplifyVwPreserve<f64> for Polygon<f64> {
    fn simplify_vw_preserve(&self, epsilon: f64) -> Self {
        // Take &self and return a new Polygon
        // Divide into segments between convex hull vertices
        let hull_indices = self.exterior().convex_hull_indices();
        let coord_vec = self.exterior().clone().into_inner();
        let segments = hull_indices
            .windows(2)
            .map(|window| match window {
                &[start, end] => LineString::new(coord_vec[start..=end].to_vec()),
                _ => unreachable!(),  // window is always &[usize, usize]
            })
            .collect::<Vec<LineString<f64>>>();

        // Reduce line segments and merge
        let reduced_segments = segments
            .par_iter()  // parallelize with rayon
            .map(|ls| ls.simplify_vw_preserve(epsilon))
            .collect::<Vec<LineString<f64>>>();

        let mut exterior: Vec<Coord<f64>> = vec![];
        for (i, ls) in reduced_segments.into_iter().enumerate() {
            if i == 0 {
                exterior.extend(&ls.clone().into_inner());
            } else {
                exterior.extend(&ls.clone().into_inner()[1..]);
            }
        }

        Polygon::new(LineString::new(exterior), vec![])
    }
}
