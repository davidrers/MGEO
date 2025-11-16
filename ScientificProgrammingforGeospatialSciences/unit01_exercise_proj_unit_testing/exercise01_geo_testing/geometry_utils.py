from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


class InvalidGeometryError(Exception):
    """Custom exception for invalid geometries."""
    pass


# ----------------------------------------------------
# STEP 1 – make_square
# ----------------------------------------------------
def make_square(x, y, size):
    """Return a square polygon centered on (x, y)."""
    # STEP 1: implement in Part 2

    # Validate size
    if size <= 0:
        raise ValueError("Size must be positive.")

    half = size / 2.0

    # Construct square coordinates
    coords = [
        (x - half, y - half),
        (x + half, y - half),
        (x + half, y + half),
        (x - half, y + half),
        (x - half, y - half),  # close polygon
    ]

    return Polygon(coords)


# ----------------------------------------------------
# STEP 2 – is_valid_geometry
# ----------------------------------------------------
def is_valid_geometry(geom):
    """Return True if geom is not None and geom.is_valid."""
    # STEP 2: implement in Part 2
    if geom is None:
        return False
    return geom.is_valid


# ----------------------------------------------------
# STEP 3 – union_geometries
# ----------------------------------------------------
def union_geometries(geoms):
    """Return unary union of a list of geometries.
    Raise InvalidGeometryError if any is invalid.
    """
    # STEP 3: implement in Part 2
    # Validate input
    if type(geoms) is not list:
        raise TypeError("Input must be a list of geometries.")

    for g in geoms:
        if not is_valid_geometry(g):
            raise InvalidGeometryError("Invalid geometry detected.")

    return unary_union(geoms)


# ----------------------------------------------------
# STEP 4 – buffer_point
# ----------------------------------------------------
def buffer_point(x, y, dist):
    """Create a point and buffer it by dist (dist >= 0)."""
    # STEP 4: implement in Part 2
    if dist < 0:
        raise ValueError("Distance must be non-negative.")

    p = Point(x, y)
    return p.buffer(dist)