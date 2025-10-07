#
# Copyright 2025- European Centre for Medium-Range Weather Forecasts (ECMWF)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#
# Copyright 2025- Niall Oswald and Kenneth Martin and Jo Wayne Tan
#


import pickle
from pathlib import Path

import typer
from matplotlib import pyplot as plt
from polyshell import ReductionMethod, ReductionMode, reduce_polygon

app = typer.Typer(no_args_is_help=True)


@app.command()
def plot_reduction(
    path: Path, mode: ReductionMode, val: float, method: ReductionMethod
):
    """Plot a polygon and its reduction."""
    with open(path, "rb") as f:
        original_poly = pickle.load(f)

    reduced_poly = reduce_polygon(original_poly, mode, val, method)

    # Report reduction
    print(f"Reduction rate: {len(reduced_poly)} / {len(original_poly)}")

    # Extract data
    x_orig, y_orig = zip(*original_poly)
    x_reduced, y_reduced = zip(*reduced_poly)

    # Plot original and reduced polygons
    plt.plot(x_orig, y_orig, "b-")
    plt.plot(x_reduced, y_reduced, "r-")
    plt.show()


if __name__ == "__main__":
    app()
