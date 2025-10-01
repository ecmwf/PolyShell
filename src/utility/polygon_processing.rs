use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;


#[pyfunction]
pub fn is_clockwise(poly: Vec<[f64; 2]>) -> PyResult<bool> {
    let n = poly.len();
    if n < 3 {
        return Err(PyValueError::new_err("Polygon must have at least 3 points."));
    }

    let mut signed_area: f64 = 0.0;

    for i in 0..n {
        let [x1, y1] = poly[i];
        let [x2, y2] = poly[(i + 1) % n];
        signed_area += x1 * y2 - x2 * y1;
    }

    if signed_area < 0.0 {
        Ok(true)
    } else if signed_area > 0.0 {
        Ok(false)
    } else {
        Err(PyValueError::new_err("Polygon is degenerate."))
    }
}
