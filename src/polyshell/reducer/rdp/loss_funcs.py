"""Loss functions for the Ramer–Douglas–Peucker line reduction algorithm."""

from typing import Protocol

from polyshell.geometry import Triangle


class LossFunction(Protocol):
    """Schema for loss functions in the Ramer–Douglas–Peucker algorithm."""

    def __call__(self, triangle: Triangle) -> float:
        """Compute the loss of a triangle.

        Loss must share the sign of the signed area.
        """
        ...


def signed_area(triangle: Triangle) -> float:
    return triangle.signed_area()
