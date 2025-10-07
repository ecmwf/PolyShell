# Installation

## Download from PyPI

PolyShell binaries are published on [PyPI]() and are available for all major platforms.

Install PolyShell using your package manager of choice:

=== "pip"

    <!-- termynal -->

    ```
    $ pip install polyshell
    ```

=== "uv"

    <!-- termynal -->

    ```
    $ uv add polyshell
    ```

---

## Build from source

To build PolyShell from source both a [functioning Rust compiler](https://www.rust-lang.org/tools/install) and
[maturin](https://www.maturin.rs/) must be installed.

### maturin

PolyShell is built natively using the maturin build system.

For development, PolyShell can be installed in [editable mode](https://peps.python.org/pep-0660/) to an activated
virtual environment using the `maturin develop` command.

<!-- termynal -->

```
# Clone the PolyShell source
$ git clone https://github.com/ECMWFCode4Earth/PolyShell.git
$ cd PolyShell
# Create and activate a virtual environment
$ python -m venv
$ source venv/bin/activate
# Install into the virtual environment
$ maturin develop
```

!!! tip

    To build a binary wheel with optimization enabled run:
    ```
    maturin build --release
    ```

### uv

While builds can be managed directly with maturin, we recommended to instead use the interface provided
by [uv](https://docs.astral.sh/uv/).

As PolyShell is managed as project through uv, development hooks have been configured to the build process to the build
process as seamless as possible.

<!-- termynal -->

```
# Clone the PolyShell source
$ git clone https://github.com/ECMWFCode4Earth/PolyShell.git
$ cd PolyShell
# Sync packages with uv
$ uv sync
```

uv automatically detects changes to the source and recompiles when necessary.

!!! tip

    By default uv will build PolyShell with optimisations enabled. To disable optimizations uncomment the following
    line in the `pyproject.toml` file:

    ```toml
    [tool.uv]
    # Rebuild package when any rust files change
    cache-keys = [{ file = "pyproject.toml" }, { file = "rust/Cargo.toml" }, { file = "**/*.rs" }]
    # Uncomment to build rust code in development mode
    config-settings = { build-args = '--profile=dev' }  # <- Uncomment this line!
    ```
