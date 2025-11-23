import copy
import pytest

# Change this import to your actual function/module name
# from game_of_life import next_generation
from game_of_life import next_generation  # noqa: F401  # <- update if needed


def test_next_generation_from_given_grid():
    # Arrange
    grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [1, 0, 0, 1, 0],
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 0],
    ]
    grid_before = copy.deepcopy(grid)

    # Expected next grid (Conway’s rules)
    expected = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]

    # Act
    out = next_generation(grid)

    # Assert
    assert out == expected, "Next generation grid does not match expected result."
    assert grid == grid_before, "Function should not mutate the input grid."
    assert len(out) == len(grid) and all(len(r) == len(grid[0]) for r in out), "Output shape must match input."
