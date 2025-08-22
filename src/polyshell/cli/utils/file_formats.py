import pickle
from pathlib import Path

from polyshell.geometry import Polygon


def load_from_path(path: Path) -> Polygon:
    if path.suffix in supported_formats:
        return supported_formats[path.suffix].load(path)
    else:
        raise FileNotFoundError("Unsupported file format")


def save_to_path(polygon: Polygon, output_path: Path):
    if output_path.suffix in supported_formats:
        supported_formats[output_path.suffix].save(polygon, output_path)
    else:
        raise FileNotFoundError("Unsupported file format")


class FileFormat:
    """Base class for file formats with can load and store polygons."""

    @staticmethod
    def load(path: Path) -> Polygon:
        raise NotImplementedError()

    @staticmethod
    def save(data: Polygon, path: Path):
        raise NotImplementedError()


class PickleFileFormat(FileFormat):
    @staticmethod
    def load(path: Path) -> Polygon:
        with open(path, "rb") as f:
            return Polygon.from_array(pickle.load(f))

    @staticmethod
    def save(data: Polygon, path: Path):
        with open(path, "wb") as f:
            pickle.dump(data.to_array(), f)


supported_formats = {".pkl": PickleFileFormat}