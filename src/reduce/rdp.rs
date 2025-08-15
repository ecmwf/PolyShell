use crate::convex_hull::melkman::melkman_indices;
use crate::extensions::geo_ext::OrdTriangle;
use geo::{Area, Coord, GeoFloat, Intersects, Line, LineString, Polygon};
use rayon::prelude::*;
use rstar::primitives::CachedEnvelope;
use rstar::{RTree, RTreeNum, RTreeObject};

fn rdp_preserve<T>(ls: &[Coord<T>], eps: T, tree: &RTree<CachedEnvelope<Line<T>>>) -> Vec<Coord<T>>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    let (first, last) = match ls {
        [] => return vec![],
        &[only] => return vec![only],
        &[first, last] => return vec![first, last],
        &[first, .., last] => (first, last),
    };

    let (farthest_index, farthest_distance) = ls
        .iter()
        .enumerate()
        .take(ls.len() - 1)
        .skip(1)
        .map(|(index, &coord)| (index, OrdTriangle(first, coord, last).signed_area()))
        .fold(
            (0usize, T::zero()),
            |(farthest_index, farthest_distance), (index, distance)| {
                if farthest_distance < T::zero() {
                    if distance < farthest_distance {
                        return (index, distance);
                    }
                } else if distance.abs() >= farthest_distance.abs() {
                    return (index, distance);
                };
                (farthest_index, farthest_distance)
                // if distance.abs() >= farthest_distance.abs() {
                //     (index, distance)
                // } else {
                //     (farthest_index, farthest_distance)
                // }
            },
        );

    let first_last_line = CachedEnvelope::new(Line::new(first, last));

    // if farthest_distance >= T::zero() && tree_intersect(first_last_line, tree) {
    //     println!("Self intersection at {:?}", *first_last_line);
    //     println!("Furthest distance {:?}", farthest_distance);
    //     return vec![first, last];
    // }

    if farthest_distance < T::zero()
        || farthest_distance > eps
        || tree_intersect(first_last_line, tree)
    {
        let (mut left, right) = rayon::join(
            || rdp_preserve(&ls[..=farthest_index], eps, tree),
            || rdp_preserve(&ls[farthest_index..], eps, tree),
        );

        left.pop();
        left.extend_from_slice(&right);

        return left;
    }

    vec![first, last]
}

fn tree_intersect<T>(line: CachedEnvelope<Line<T>>, tree: &RTree<CachedEnvelope<Line<T>>>) -> bool
where
    T: GeoFloat + RTreeNum,
{
    let (start, end) = line.points();
    let bounding_rect = line.envelope();

    tree.locate_in_envelope_intersecting(&bounding_rect)
        .any(|candidate| {
            let (candidate_start, candidate_end) = candidate.points();
            candidate_start.0 != start.0
                && candidate_start.0 != end.0
                && candidate_end.0 != start.0
                && candidate_end.0 != end.0
                && line.intersects(&**candidate)
        })
}

pub trait SimplifyRDPPreserve<T, Epsilon = T> {
    fn simplify_rdp_preserve(&self, epsilon: Epsilon) -> Self;
}

impl<T> SimplifyRDPPreserve<T> for LineString<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_rdp_preserve(&self, epsilon: T) -> Self {
        let tree: RTree<CachedEnvelope<_>> =
            RTree::bulk_load(self.lines().map(CachedEnvelope::new).collect::<Vec<_>>());

        LineString::new(rdp_preserve(&self.0, epsilon, &tree))
    }
}

impl<T> SimplifyRDPPreserve<T> for Polygon<T>
where
    T: GeoFloat + RTreeNum + Send + Sync,
{
    fn simplify_rdp_preserve(&self, epsilon: T) -> Self {
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
            .map(|ls| ls.simplify_rdp_preserve(epsilon))
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
