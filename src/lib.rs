use crate::extensions::validation::InvalidPolygon;
use algorithms::simplify_charshape::SimplifyCharshape;
use algorithms::simplify_rdp::SimplifyRDP;
use algorithms::simplify_vw::SimplifyVW;
use extensions::validation::Validate;
use geo::{Polygon, Winding};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

mod algorithms;
mod extensions;

impl From<InvalidPolygon> for PyErr {
    fn from(err: InvalidPolygon) -> Self {
        PyValueError::new_err(err.to_string())
    }
}

#[pyfunction]
fn reduce_polygon_vw(orig: Vec<[f64; 2]>, eps: f64, len: usize) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let mut polygon = Polygon::new(orig.into(), vec![]).validate()?;
    polygon.exterior_mut(|ls| ls.make_cw_winding());

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_vw(eps, len).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_vw_unchecked(
    orig: Vec<[f64; 2]>,
    eps: f64,
    len: usize,
) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(orig.into(), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_vw(eps, len).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_char(orig: Vec<[f64; 2]>, eps: f64, len: usize) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(orig.into(), vec![]).validate()?;

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_charshape(eps, len).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_char_unchecked(
    orig: Vec<[f64; 2]>,
    eps: f64,
    len: usize,
) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(orig.into(), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_charshape(eps, len).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_rdp(orig: Vec<[f64; 2]>, eps: f64) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let mut polygon = Polygon::new(orig.into(), vec![]).validate()?;
    polygon.exterior_mut(|ls| ls.make_cw_winding());

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_rdp(eps).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_rdp_unchecked(orig: Vec<[f64; 2]>, eps: f64) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(orig.into(), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_rdp(eps).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pymodule]
fn _polyshell(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reduce_polygon_vw, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_char, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_rdp, m)?)?;

    m.add_function(wrap_pyfunction!(reduce_polygon_vw_unchecked, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_char_unchecked, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_rdp_unchecked, m)?)?;

    Ok(())
}
