use geo::{Coord, CoordsIter, GeoNum, Kernel, Orientation, Polygon};
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

fn melkman<T: GeoNum>(poly: &Polygon<T>) -> Vec<(usize, Coord<T>)> {
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
    hull.into()
}

pub trait Melkman<T: GeoNum> {
    fn hull_indices(&self) -> Vec<usize>;
}

impl<T: GeoNum> Melkman<T> for Polygon<T> {
    fn hull_indices(&self) -> Vec<usize> {
        melkman(self).into_iter().map(|(index, _)| index).collect()
    }
}

#[cfg(test)]
mod test {
    use crate::algorithms::melkman::Melkman;
    use geo::polygon;

    #[test]
    fn simple_test() {
        let poly = polygon![
            (x: 0.0, y: 0.0),
            (x: 0.0, y: 1.0),
            (x: 0.5, y: 0.5),
            (x: 1.0, y: 1.0),
            (x: 1.0, y: 0.0),
        ];
        let hull = poly.hull_indices();
        let correct = vec![4, 0, 1, 3, 4];
        assert_eq!(hull, correct);
    }
}
