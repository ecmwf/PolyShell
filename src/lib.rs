use algorithms::charshape::SimplifyCharshape;
use algorithms::rdp::SimplifyRDP;
use algorithms::vw::SimplifyVW;
use geo::Polygon;
use pyo3::prelude::*;

mod algorithms;
mod extensions;

#[pyfunction]
fn reduce_polygon_vw(orig: Vec<[f64; 2]>, eps: f64) -> PyResult<Vec<(f64, f64)>> {
    // Instantiate a Polygon from a Vec of coordinates
    let polygon = Polygon::new(orig.into(), vec![]);

    // Reduce and extract coordinates
    let (exterior, _) = polygon.simplify_vw(eps).into_inner();
    let coords = exterior.into_iter().map(|c| c.x_y()).collect::<Vec<_>>();

    Ok(coords)
}

#[pyfunction]
fn reduce_polygon_char(orig: Vec<[f64; 2]>, eps: f64, len: usize) -> PyResult<Vec<(f64, f64)>> {
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
    Ok(())
}
