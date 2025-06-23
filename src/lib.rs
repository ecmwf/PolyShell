use geo::{LineString, Polygon};
use pyo3::prelude::*;
use reduce::{polygon_to_points, SimplifyVwPreserve};

mod reduce;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn reduce_polygon(orig: Vec<[f64; 2]>, epsilon: f64) -> PyResult<Vec<[f64; 2]>> {
    let polygon = Polygon::new(LineString::from(orig), vec![]);
    let red_polygon = polygon.simplify_vw_preserve(epsilon);

    Ok(polygon_to_points(&red_polygon))
}

/// A Python module implemented in Rust.
#[pymodule]
fn polyshell(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reduce_polygon, m)?)?;
    Ok(())
}
