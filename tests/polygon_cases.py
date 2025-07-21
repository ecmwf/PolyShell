"""Cases for end-to-end testing of reduce_polygon."""

import pickle

from polyshell.geometry import Polygon


class CaseLarge:
    """Polygons with a very large number of vertices."""

    def case_ionian_sea(self) -> Polygon:
        """Polygon generated from the Ionian Sea."""
        with open("tests/data/sea/ionian_sea.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    def case_afro_eurasia(self) -> Polygon:
        """Polygon generated from the Afro-Eurasia land mass."""
        with open("tests/data/land/afro_eurasia.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    def case_americas(self) -> Polygon:
        """Polygon generated from the Americas land mass."""
        with open("tests/data/land/americas.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    def case_antarctica(self) -> Polygon:
        """Polygon generated from the Antarctic continent."""
        with open("tests/data/land/antarctica.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    def case_baffin_island(self) -> Polygon:
        """Polygon generated from Baffin island."""
        with open("tests/data/land/baffin_island.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))

    def case_greenland(self) -> Polygon:
        """Polygon generated from Greenland."""
        with open("tests/data/land/greenland.pkl", "rb") as f:
            return Polygon.from_array(pickle.load(f))


class CaseSmall:
    """Polygons with a small number of vertices."""

    class CaseSelfIntersection:
        """Minimal polygons prone to self intersection."""

        def case_interlocking_teeth(self) -> Polygon:
            """Two interlocking teeth with a narrow channel in-between."""
            return Polygon.from_array(
                [
                    (0.0, 0.0),
                    (0.0, 1.0),
                    (0.25, 1.0),
                    (0.05, 0.9),
                    (0.25, 0.8),
                    (0.25, 0.25),
                    (0.75, 0.25),
                    (0.75, 0.8),
                    (0.15, 0.9),
                    (0.75, 1.0),
                    (1.0, 1.0),
                    (1.0, 0.0),
                    (0.0, 0.0),
                ]
            )
