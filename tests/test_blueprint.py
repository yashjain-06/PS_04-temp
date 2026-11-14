import json
from src.env.blueprint import BlueprintError, load_blueprint, parse_ascii, parse_blueprint
import pytest

BLUEPRINTS = ["simple_wall", "wall_with_opening", "double_wall", "u_shape"]


def test_shipped_blueprints_load():
    for n in BLUEPRINTS:
        bp = load_blueprint(f"blueprints/{n}.json")
        assert bp.cells and bp.depots and bp.obstacles and bp.depth == 1


def test_opening_blueprint_has_a_gap():
    bp = load_blueprint("blueprints/wall_with_opening.json")
    xs = sorted(x for x, _, _ in bp.cells)
    assert (14 not in xs) and (15 not in xs) and 13 in xs and 16 in xs


def test_ascii_format_roundtrip():
    bp = parse_ascii("D...X\n.###.\n.....\n", "tiny")
    assert bp.targets == {(1, 1), (2, 1), (3, 1)} and bp.depots == ((0, 0),) and bp.obstacles == ((4, 0),)


def test_rejects_bad_blueprints():
    base = {"width": 5, "height": 5, "depots": [[0, 0]], "cells": [[2, 2, 0]]}
    parse_blueprint(base)
    for bad in ({**base, "cells": [[9, 9, 0]]}, {**base, "cells": []}, {**base, "depots": []},
                {**base, "cells": [[2, 2, 1]]}, {**base, "obstacles": [[2, 2]]}, {**base, "cells": [[2, 2, 0], [2, 2, 0]]}):
        with pytest.raises(BlueprintError):
            parse_blueprint(bad)
