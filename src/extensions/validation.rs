use geo::sweep::{Cross, Intersections};
use geo::{GeoFloat, GeoNum, HasDimensions, Line, Polygon};
use std::error::Error;
use std::fmt;

#[derive(Debug)]
pub enum InvalidPolygon {
    TooFewPoints,
    OpenChain,
    SelfIntersection,
    NonFiniteCoord(usize),
}

impl fmt::Display for InvalidPolygon {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            InvalidPolygon::TooFewPoints => {
                write!(f, "Polygon must have at least 3 distinct points")
            }
            InvalidPolygon::OpenChain => write!(f, "Polygon is not closed"),
            InvalidPolygon::SelfIntersection => write!(f, "Polygon has a self-intersection"),
            InvalidPolygon::NonFiniteCoord(index) => {
                write!(f, "Polygon has a non-finite coordinate at index {index}")
            }
        }
    }
}

impl Error for InvalidPolygon {}

#[derive(Clone, Debug)]
struct IndexedLine<T: GeoNum> {
    index: usize,
    line: Line<T>,
}

impl<T: GeoFloat> Cross for IndexedLine<T> {
    type Scalar = T;
    fn line(&self) -> Line<T> {
        self.line
    }
}

pub trait Validate: Sized {
    fn check_validate(&self) -> Result<(), InvalidPolygon>;

    fn is_valid(&self) -> bool {
        self.check_validate().is_ok()
    }

    fn validate(self) -> Result<Self, InvalidPolygon> {
        match self.check_validate() {
            Ok(()) => Ok(self),
            Err(e) => Err(e),
        }
    }
}

impl<T: GeoFloat> Validate for Polygon<T> {
    fn check_validate(&self) -> Result<(), InvalidPolygon> {
        let ls = self.exterior();

        // Check number of points
        if self.is_empty() {
            return Ok(());
        }
        if ls.0.len() < 4 {
            return Err(InvalidPolygon::TooFewPoints);
        }

        // Check for closure
        if ls.0.first() != ls.0.last() {
            return Err(InvalidPolygon::OpenChain);
        }

        // Check for finite-ness
        for (index, coord) in ls.0.iter().enumerate() {
            if !(coord.x.is_finite() && coord.y.is_finite()) {
                return Err(InvalidPolygon::NonFiniteCoord(index));
            }
        }

        // Check for self-intersections
        let lines = ls
            .lines()
            .enumerate()
            .map(|(index, line)| IndexedLine { index, line });

        let intersections_iter = Intersections::from_iter(lines);

        for (line1, line2, _) in intersections_iter {
            let idx1 = line1.index;
            let idx2 = line2.index;

            if (idx1 as isize - idx2 as isize).abs() > 1 && idx1 + idx2 + 2 < ls.0.len() {
                return Err(InvalidPolygon::SelfIntersection);
            }
        }

        Ok(())
    }
}
