use geo::algorithm::Area;
use geo::geometry::{Coord, LineString, Point, Triangle};
use geo::{CoordFloat, CoordNum};

// geo::Triangle sorts the vertices so they are always oriented ccw
// this is not acceptable for our use case
#[derive(Copy, Clone, Hash, Eq, PartialEq)]
pub struct OrdTriangle<T: CoordNum = f64>(pub Coord<T>, pub Coord<T>, pub Coord<T>);

impl<T: CoordNum> OrdTriangle<T> {
    pub fn new(v1: Coord<T>, v2: Coord<T>, v3: Coord<T>) -> Self {
        Self(v1, v2, v3)
    }
}

impl<T: CoordNum> Into<Triangle<T>> for OrdTriangle<T> {
    fn into(self) -> Triangle<T> {
        Triangle::new(self.0, self.1, self.2)
    }
}

impl<T: CoordFloat> Area<T> for OrdTriangle<T> {
    fn signed_area(&self) -> T {
        Point::from(self.0).cross_prod(self.1.into(), self.2.into()) / (T::one() + T::one())
    }

    fn unsigned_area(&self) -> T {
        self.signed_area().abs()
    }
}

pub trait LineStringExt<T: CoordNum> {
    fn ord_triangles(&'_ self) -> impl ExactSizeIterator<Item = OrdTriangle<T>> + '_;
}

impl<T: CoordNum> LineStringExt<T> for LineString<T> {
    fn ord_triangles(&'_ self) -> impl ExactSizeIterator<Item = OrdTriangle<T>> + '_ {
        self.0.windows(3).map(|w| unsafe {
            OrdTriangle::new(
                *w.get_unchecked(0),
                *w.get_unchecked(1),
                *w.get_unchecked(2),
            )
        })
    }
}
