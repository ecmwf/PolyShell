use geo::{CoordsIter, GeoNum, Kernel, Orientation, Polygon};
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
            T::Ker::orient2d(v, hull.front().unwrap().1, hull.front_less().unwrap().1),
            Orientation::CounterClockwise
        ) || matches!(
            T::Ker::orient2d(v, hull.back().unwrap().1, hull.back_less().unwrap().1),
            Orientation::Clockwise
        ) {
            while let Orientation::CounterClockwise =
                T::Ker::orient2d(v, hull.front().unwrap().1, hull.front_less().unwrap().1)
            {
                hull.pop_front();
            }
            while let Orientation::Clockwise =
                T::Ker::orient2d(v, hull.back().unwrap().1, hull.back_less().unwrap().1)
            {
                hull.pop_back();
            }

            hull.push_front((index, v));
            hull.push_back((index, v));
        };
    }

    hull.into_iter().map(|(index, _)| index).collect()
}
