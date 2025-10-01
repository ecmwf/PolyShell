# PolyShell

A high-performance coverage-preserving polygon reduction library for Python, written in Rust.

![Benchmark](assets/Benchmark-Light.svg#only-light)
![Benchmark](assets/Benchmark-Dark.svg#only-dark)
/// caption
Time to reduce a 50,000 point polygon by 90%.
///

---

## Highlights

- ✅ Guarantees encapsulation of the initial polygon.
- 🔥 Rust-powered performance.
- 🧩 A simple Python API to access all reduction methods and modes.
- 🌍 Seamlessly integration with [NumPy](https://numpy.org/) and [Shapely](https://shapely.readthedocs.io/).
- 📏 Tunable accuracy and reduction rates.
- 🐍 Python and [PyPy](https://pypy.org/) compatible.

PolyShell is supported by the [ECMWF](https://www.ecmwf.int/) through
the [Code for Earth programme](https://codeforearth.ecmwf.int/).

---

## Installation

PolyShell is available on [PyPI](https://pypi.org/) for easy installation:

<!-- termynal -->

```
$ pip install polyshell
---> 100%
Successfully installed polyshell
```

PolyShell can also be built from source using [maturin](https://www.maturin.rs/).
See the guide [here](./user-guide/installation.md#build-from-source).

---

## Example

All of PolyShell's reduction algorithms are accessible through `reduce_polygon`.

=== "Python 3.10+"

    ```python
    from polyshell import reduce_polygon

    original = [
        (0.0, 0.0),
        (0.0, 1.0),
        (0.5, 0.5),
        (1.0, 1.0),
        (1.0, 0.0),
        (0.0, 0.0),
    ]

    reduced = reduce_polygon(original, "auto", method="vw")
    ```

For all the available options, see the [full list of features](user-guide/features.md).

---

## Learn more

For more information see the [guide](user-guide/index.md).
