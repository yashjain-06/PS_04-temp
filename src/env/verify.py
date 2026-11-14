"""Correctness check of the finished structure (owner: M1)."""
from __future__ import annotations

from src.experiments import metrics as M


def accuracy(model) -> float:
    return M.accuracy(model.structure_cells(), model.blueprint_cells())


def verify_structure(model) -> dict:
    st, bp = model.structure_cells(), model.blueprint_cells()
    return {"accuracy": M.accuracy(st, bp), "exact": M.is_exact(st, bp), "extra_cells": M.extra_cells(st, bp)}
