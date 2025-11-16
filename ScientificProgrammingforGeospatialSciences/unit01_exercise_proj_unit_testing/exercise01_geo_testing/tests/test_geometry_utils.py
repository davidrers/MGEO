# tests/test_geometry_utils.py
import pytest
from shapely.geometry import Point, Polygon
from geometry_utils import (
    make_square,
    is_valid_geometry,
    union_geometries,
    buffer_point,
    InvalidGeometryError,
)

# ==== STEP T1: tests for make_square ====

def test_make_square_valid_polygon():
    """Square with positive size should be a valid polygon of 4 points."""
    # TODO: students complete

    #Create a square
    s = make_square(0, 0, 4)

    # Validate if its a geometry.Polygon instance
    assert isinstance(s, Polygon)
    # Check if the polygon is valid
    assert s.is_valid
    # Check the area gives the correct 
    assert s.area == pytest.approx(16.0)

    # Check number of coordinates
    assert len(s.exterior.coords) == 5

def test_make_square_raises_on_nonpositive_size():
    with pytest.raises(ValueError):
        make_square(0, 0, 0)

# ==== STEP T2: tests for is_valid_geometry ====

def test_is_valid_geometry_none_returns_false():
    result = is_valid_geometry(None)
    assert result is False

def test_is_valid_geometry_invalid_polygon_returns_false():
    # Hint: self-intersecting polygon
    poly = Polygon([(0,0), (1,1), (1,0), (0,1), (0,0)])
    result = is_valid_geometry(poly)
    assert result is False

# ==== STEP T3: tests for union_geometries ====

def test_union_geometries_raises_on_invalid():
    bad = Polygon([(0,0), (1,1), (1,0), (0,1), (0,0)])
    with pytest.raises(InvalidGeometryError):
        union_geometries([bad])

def test_union_geometries_returns_union_of_valid_geometries():
    """TODO: students implement a happy-path union test."""
    # Hint: try unioning two separate squares and check the total area.
    # TODO
    s1 = make_square(0, 0, 2)
    s2 = make_square(5, 0, 2)  

    union = union_geometries([s1, s2])
    #Check if the union is valid
    assert union.is_valid

    #Check whether the total area is equal to the sum of individual areas
    expected_area = s1.area + s2.area 
    assert union.area == pytest.approx(expected_area)

# ==== STEP T4: tests for buffer_point ====

def test_buffer_point_raises_on_negative_distance():
    with pytest.raises(ValueError):
        buffer_point(0, 0, -1)

def test_buffer_point_returns_geometry():
    g = buffer_point(0, 0, 1.0)
    assert g.is_valid
    assert g.area > 0
