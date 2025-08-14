# PolyShell

A high-performance coverage-preserving polygon reduction library for Python, written in Rust.

---

## Highlights

- ✅ **Coverage Guarantees** — guarantees coverage of the initial polygon.
- ⚡ **Rust-powered performance** — optimized algorithms for large datasets.
- 🧩 **Simple Python API** — integrates into data science, GIS, and graphics pipelines.
- 🌍 **Geospatial ready** — works seamlessly with [Shapely](https://shapely.readthedocs.io/) and [GeoPandas](https://geopandas.org/).
- 📏 **Customizable** — control simplification levels and precision.
- 🐍 **PyPy compatible** — out-of-the-box support for CPython and [PyPy](https://pypy.org/).

---

## Installation

PolyShell is available on [PyPI](https://pypi.org/) for easy installation:

=== "pip"

    ```console
    $ pip install polyshell
    ```

=== "uv"

    ```console
    $ uv add polyshell
    ```

Alternatively, PolyShell can also be built from source using [maturin](https://www.maturin.rs/). See the guide [here].

---

## Example

=== "Python 3.8+"

    ```python
    from polyshell import reduce_polygon
    ```


---

## Why PolyShell?

Polygon simplification is common in graphics, GIS, and computational geometry, but most algorithms risk cutting *into* the original shape — potentially losing important areas. PolyShell takes a different approach:

- **Coverage-preserving** — the reduced polygon is guaranteed to completely enclose the original.
- **High-performance** — written in Rust and exposed via Python for minimal overhead.
- **Consistent & Robust** — works reliably with both simple and complex polygons.

