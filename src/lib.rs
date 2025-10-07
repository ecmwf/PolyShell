// Copyright 2025- European Centre for Medium-Range Weather Forecasts (ECMWF)

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// In applying this licence, ECMWF does not waive the privileges and immunities
// granted to it by virtue of its status as an intergovernmental organisation nor
// does it submit to any jurisdiction.

// Copyright 2025- Niall Oswald and Kenneth Martin and Jo Wayne Tan

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

#[pyfunction]
fn is_valid(poly: Vec<[f64; 2]>) -> PyResult<bool> {
    let poly = Polygon::new(poly.into(), vec![]);
    Ok(poly.is_valid() && poly.exterior().is_cw())
}

#[pymodule]
fn _polyshell(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reduce_polygon_vw, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_char, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_rdp, m)?)?;

    m.add_function(wrap_pyfunction!(reduce_polygon_vw_unchecked, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_char_unchecked, m)?)?;
    m.add_function(wrap_pyfunction!(reduce_polygon_rdp_unchecked, m)?)?;

    m.add_function(wrap_pyfunction!(is_valid, m)?)?;

    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
