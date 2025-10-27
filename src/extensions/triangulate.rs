use geo::{CoordsIter, GeoNum, Polygon};
use spade::{ConstrainedDelaunayTriangulation, Point2, SpadeNum};

pub trait Triangulate<T: SpadeNum> {
    fn triangulate(&self) -> ConstrainedDelaunayTriangulation<Point2<T>>;
}

impl<T> Triangulate<T> for Polygon<T>
where
    T: SpadeNum + GeoNum,
{
    fn triangulate(&self) -> ConstrainedDelaunayTriangulation<Point2<T>> {
        let num_vertices = self.exterior().0.len() - 1;

        let vertices = self
            .exterior_coords_iter()
            .take(num_vertices) // duplicate points are removed
            .map(|c| Point2::new(c.x, c.y))
            .collect();

        let edges = (0..num_vertices)
            .map(|i| {
                if i == 0 {
                    [num_vertices - 1, 0]
                } else {
                    [i - 1, i]
                }
            })
            .collect();

        ConstrainedDelaunayTriangulation::<Point2<T>>::bulk_load_cdt(vertices, edges).unwrap()
    }
}
