# PolyShell

<div align="center">

[![Static Badge](https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg)](https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE)
[![Static Badge](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/emerging_badge.svg)](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity)
![PyPI - Version](https://img.shields.io/pypi/v/polyshell)
![Build Status](https://img.shields.io/github/actions/workflow/status/ECMWFCode4Earth/PolyShell/CI.yml)
![Docs Build Status](https://img.shields.io/github/actions/workflow/status/ECMWFCode4Earth/PolyShell/publish-docs.yml?label=docs)
</div>

A high-performance coverage-preserving polygon reduction library for Python, written in Rust.

> \[!IMPORTANT\]
> This software is **Emerging** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).

<p align="center">
  <picture align="center">
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/Benchmark-Dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/ecmwf/PolyShell/refs/heads/main/docs/assets/Benchmark-Dark.svg">
    <img alt="Shows a bar chart with benchmark results." src="https://raw.githubusercontent.com/ecmwf/PolyShell/refs/heads/main/docs/assets/Benchmark-Light.svg">
  </picture>
</p>

<p align="center">
  <i>Time to reduce a 50,000 point polygon by 90%.</i>
</p>

_This project was developed as part of ECMWF's Code4Earth initiative by Niall Oswald, Kenneth Martin and Jo Wayne Tan._

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

```console
$ pip install polyshell
```

PolyShell can also be built from source using [maturin](https://www.maturin.rs/). See the
guide [here](https://ecmwf.github.io/PolyShell/user-guide/installation/).

---

## Example

All of PolyShell's reduction algorithms are accessible through `reduce_polygon`.

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

For all the available options, see
the [full list of features](https://ecmwf.github.io/PolyShell/user-guide/features/).

---

## Learn more

For more information see the [guide](https://ecmwf.github.io/PolyShell/user-guide/).

