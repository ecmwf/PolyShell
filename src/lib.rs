use crate::reduce::char_shape::SimplifyCharshape;
use crate::reduce::vw_preserve::SimplifyVwPreserve;
use geo::{LineString, Polygon};
use pyo3::prelude::*;

mod convex_hull;
mod extensions;
mod reduce;

#[pyfunction]
fn reduce_polygon_vw(orig: Vec<[f64; 2]>, epsilon: f64) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(LineString::from(orig), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_vw_preserve(epsilon).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_char(orig: Vec<[f64; 2]>, epsilon: f64) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(LineString::from(orig), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_charshape(epsilon).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pymodule]
fn polyshell(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reduce_polygon_vw, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_char, m)?)?;
    Ok(())
}
