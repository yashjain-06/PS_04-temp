"""Shared type aliases (owner: M1)."""
Cell = tuple      # (x, y)  — flat 2D grid; z is always 0 in this project
Route = list      # list[Cell], excludes the start cell, includes the goal
