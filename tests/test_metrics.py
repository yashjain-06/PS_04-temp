import pytest
from src.experiments import metrics as m


def test_accuracy_partial_and_full():
    bp = [(0, 0), (1, 0), (2, 0), (3, 0)]
    assert m.accuracy([(0, 0), (1, 0)], bp) == 0.5
    assert m.accuracy(bp, bp) == 1.0


def test_exact_detects_extras():
    bp = [(0, 0), (1, 0)]
    assert m.is_exact(bp, bp)
    assert not m.is_exact(bp + [(5, 5)], bp)
    assert m.extra_cells(bp + [(5, 5)], bp) == 1


def test_efficiency_and_slowdown():
    assert m.efficiency(10, 100) == 0.1
    assert m.efficiency(10, 0) == 0.0
    assert m.slowdown(150, 100) == 1.5
    with pytest.raises(ValueError):
        m.slowdown(10, 0)


def test_build_time_incomplete():
    assert m.build_time(None, 3000) == 3000
    assert m.build_time(412, 3000) == 412
