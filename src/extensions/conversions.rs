use geo::{Coord, CoordNum};
use spade::{Point2, SpadeNum};

pub trait IntoCoord<T: CoordNum> {
    fn into_coord(self) -> Coord<T>;
}

impl<T> IntoCoord<T> for Point2<T>
where
    T: CoordNum + SpadeNum,
{
    fn into_coord(self) -> Coord<T> {
        Coord {
            x: self.x,
            y: self.y,
        }
    }
}
