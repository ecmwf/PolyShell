"""Loss functions for the Visvalingham-Whyatt line reduction algorithm."""

from typing import Protocol

from polyshell.geometry import Triangle


class LossFunction(Protocol):
    """Schema for loss functions in the Visvalingham-Whyatt algorithm."""

    def __call__(self, triangle: Triangle) -> float:
        """Compute the loss of a triangle.

        Loss must share the sign of the signed area.
        """
        ...


def signed_area(triangle: Triangle) -> float:
    return triangle.signed_area()
