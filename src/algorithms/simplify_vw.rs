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

/// Store triangle information. Score is used for ranking the priority queue which determines
/// removal order.
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

/// Area and topology preserving Visvalingam-Whyatt algorithm
/// adapted from the [geo implementation](https://github.com/georust/geo/blob/e8419735b5986f120ddf1de65ac68c1779c3df30/geo/src/algorithm/simplify_vw.rs)
///
///
fn visvalingam_preserve<T>(orig: &LineString<T>, eps: T, min_len: usize) -> Vec<Coord<T>>
where
    T: GeoFloat + RTreeNum,
{
    let max = orig.0.len();
    if max < 2 || max <= min_len || eps <= T::zero() {
        return orig.0.to_vec();
    }

    let mut len = orig.0.len();

    let tree: RTree<CachedEnvelope<_>> =
        RTree::bulk_load(orig.lines().map(CachedEnvelope::new).collect::<Vec<_>>());

    // Point adjacency. Tuple at index contains indices into `orig`. Negative values or values
    // greater than or equal to max means no next element. (0, 0) sentinel means deleted element.
    let mut adjacent: Vec<_> = (0..orig.0.len())
        .map(|i| {
            if i == 0 {
                (-1_i32, 1_i32)
            } else {
                ((i - 1) as i32, (i + 1) as i32)
            }
        })
        .collect();

    // Store all triangles in a minimum priority queue, based on signed area.
    //
    // Only triangles of positive score are pushed to the heap.
    // Invalid triangles are *not* removed when the corresponding point is removed; they are
    // invalidated using (0, 0) values in `adjacent` and skipped as necessary.
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

    // Iterate over points while there is an associated triangle with area between 0 and epsilon
    while let Some(smallest) = pq.pop() {
        if smallest.score > eps {
            // Min-heap guarantees all future points have areas greater than epsilon
            break;
        }

        if len <= min_len {
            // Further removal would send us below the minimum length
            break;
        }

        let (left, right) = adjacent[smallest.current];
        // A point in this triangle has been removed since this `VScore` was created, so skip it
        if left != smallest.left as i32 || right != smallest.right as i32 {
            continue;
        }

        // Removal of this point would cause self-intersection, so skip it
        if tree_intersect(&tree, &smallest, &orig.0) {
            continue;
        }

        let (ll, _) = adjacent[left as usize];
        let (_, rr) = adjacent[right as usize];
        adjacent[left as usize] = (ll, right);
        adjacent[right as usize] = (left, rr);
        // Remove the point from the adjacency list
        adjacent[smallest.current] = (0, 0);
        // Update the length of the linestring
        len -= 1;
        // The rtree is never updated as self-intersection can never occur with stale segments and
        // if a segment were to intersect with a new segment, then it also intersects with a stale
        // segment

        // Recompute the areas of adjacent triangles(s) using left and right adjacent points,
        // this may add new triangles to the heap
        recompute_triangles(orig, &mut pq, ll, left, right, rr, max);
    }

    // Filter out deleted points, returning remaining points
    orig.0
        .iter()
        .zip(adjacent.iter())
        .filter_map(|(tup, adj)| if *adj != (0, 0) { Some(*tup) } else { None })
        .collect()
}

/// Check whether the removal of a candidate point would cause a self-intersection.
///
/// To do this efficiently, and rtree is queried for any existing line segments which fall within
/// the bounding box of the new line segment created.
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

/// Recompute adjacent triangle(s) using left and right adjacent points, pushing to the heap
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
            // Out of bounds, i.e. we're at an end point
            continue;
        }

        let area = OrdTriangle::new(
            orig.0[ai as usize],
            orig.0[current_point as usize],
            orig.0[bi as usize],
        )
        .signed_area();

        // If removal of a point would cause a reduction in signed area, skip it
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

/// Simplifies a geometry while preserving its topology and area.
pub trait SimplifyVW<T, Epsilon = T> {
    /// Returns the simplified geometry using a topology and area preserving variant of the
    /// [Visvalingam-Whyatt](https://doi.org/10.1179/000870493786962263) algorithm.
    fn simplify_vw(&self, eps: Epsilon, len: usize) -> Self;
}

impl<T> SimplifyVW<T> for LineString<T>
where
    T: GeoFloat + RTreeNum,
{
    fn simplify_vw(&self, eps: T, len: usize) -> Self {
        LineString::from(visvalingam_preserve(self, eps, len))
    }
}

impl<T> SimplifyVW<T> for Polygon<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_vw(&self, eps: T, len: usize) -> Self {
        // Get convex hull segments, as their endpoints are invariant under reduction
        let segments = self.hull_segments();

        if len > segments.len() {
            // To reduce to a fixed length the algorithm must be synchronized
            let ls = LineString::from_segments(segments);
            let reduced_ls = ls.simplify_vw(eps, len);
            Polygon::new(reduced_ls, vec![])
        } else {
            // If a fixed length is not desired, segments can be reduced in parallel
            let reduced_segments = segments
                .into_par_iter()
                .map(|ls| ls.simplify_vw(eps, 2))
                .collect::<Vec<_>>();
            Polygon::from_segments(reduced_segments)
        }
    }
}
