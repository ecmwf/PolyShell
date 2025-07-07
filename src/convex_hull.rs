use geo::{Coord, CoordsIter, GeoNum, Orientation, Point, Polygon};
use std::cmp::Ordering;
use std::collections::VecDeque;
use std::ops::Sub;

trait SecondIndex<T> {
    fn front_less(&self) -> Option<&T>;
    fn back_less(&self) -> Option<&T>;
}

impl<T> SecondIndex<T> for VecDeque<T> {
    fn front_less(&self) -> Option<&T> {
        self.get(1)
    }

    fn back_less(&self) -> Option<&T> {
        self.get(self.len().sub(2))
    }
}

fn orientation<T>(x: Coord<T>, y: Coord<T>, z: Coord<T>) -> Orientation
where
    T: GeoNum,
{
    let (x, y, z) = (Point::from(x), Point::from(y), Point::from(z));
    match x.cross_prod(y, z).total_cmp(&T::zero()) {
        Ordering::Less => Orientation::CounterClockwise,
        Ordering::Equal => Orientation::Collinear,
        Ordering::Greater => Orientation::Clockwise,
    }
}

pub fn melkman_indices<T>(poly: &Polygon<T>) -> Vec<usize>
where
    T: GeoNum,
{
    let mut poly_iter = poly.exterior_coords_iter().enumerate();
    let x = poly_iter.next().unwrap();
    let y = poly_iter.next().unwrap();
    let mut hull = VecDeque::from([y, x, y]);

    for (index, v) in poly_iter {
        if matches!(
            orientation(v, hull.back().unwrap().1, hull.back_less().unwrap().1),
            Orientation::CounterClockwise
        ) || matches!(
            orientation(v, hull.front().unwrap().1, hull.front_less().unwrap().1),
            Orientation::Clockwise
        ) {
            while let Orientation::CounterClockwise =
                orientation(v, hull.back().unwrap().1, hull.back_less().unwrap().1)
            {
                hull.pop_back();
            }
            hull.push_back((index, v));

            while let Orientation::Clockwise =
                orientation(v, hull.front().unwrap().1, hull.front_less().unwrap().1)
            {
                hull.pop_front();
            }
            hull.push_front((index, v));
        };
    }

    hull.into_iter().map(|(index, _)| index).collect()
}
