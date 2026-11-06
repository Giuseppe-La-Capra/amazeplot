"""Tests of the row-window arithmetic (Qt-free)."""

import pytest

from amazeplot.gui.row_window import DEFAULT_PAGE_SIZE, RowWindow


def test_defaults():
    window = RowWindow()
    assert (window.start, window.size) == (0, DEFAULT_PAGE_SIZE)


@pytest.mark.parametrize(("start", "size"), [(-1, 10), (0, 0)])
def test_invalid_windows(start, size):
    with pytest.raises(ValueError):
        RowWindow(start, size)


def test_stop_never_passes_the_end():
    assert RowWindow(0, 100).stop(250) == 100
    assert RowWindow(200, 100).stop(250) == 250


def test_paging_forward_and_back():
    window = RowWindow(0, 100)
    assert not window.has_previous()
    window = window.next(250).next(250)
    assert window.start == 200
    assert not window.has_next(250)
    assert window.next(250) == window
    assert window.previous().start == 100
    assert RowWindow(30, 100).previous().start == 0


def test_clamped_after_the_table_shrinks():
    assert RowWindow(900, 100).clamped(500).start == 499
    assert RowWindow(5, 100).clamped(500).start == 5
    assert RowWindow(5, 100).clamped(0).start == 0


def test_describe():
    assert RowWindow(1000, 1000).describe(2500) == (
        "Showing rows 1,001\N{EN DASH}2,000 of 2,500"
    )
    assert RowWindow(0, 100).describe(0) == "No rows"
