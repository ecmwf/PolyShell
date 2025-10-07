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

"""Benchmarks for Visvalingam-Whyatt."""

from polyshell import reduce_polygon
from simplification.cutil import simplify_coords_vwp


def polyshell_vw(poly, eps):
    return reduce_polygon(poly, "epsilon", eps, method="vw")


def simplification_vw(poly, eps):
    return simplify_coords_vwp(poly, eps)


RUNNERS = [polyshell_vw, simplification_vw]
LABELS = ["polyshell (vw)", "simplification"]

BENCHMARKS = list(zip(RUNNERS, LABELS))
