from src.env import rules as R
from src.env.blueprint import parse_ascii
from src.env.rules import RuleSet, RuleViolation
from src.env.rules_compiler import UnbuildableError, verify_buildable
from src.env.blueprint import load_blueprint
import pytest


def rs(text):
    return RuleSet(parse_ascii(text))


def test_support_needs_seed_or_neighbour():
    r = rs("D....\n.####\n.....\n")
    assert r.is_supported(1, 1)                       # seed: target nearest the depot
    assert not r.is_supported(3, 1)                   # floating in the middle of nothing
    assert r.can_place(1, 1) and not r.can_place(3, 1)
    r.place(1, 1)
    assert r.can_place(2, 1)                          # now adjacent to a built block


def test_cannot_place_off_blueprint_or_twice():
    r = rs("D....\n.##..\n")
    assert not r.can_place(4, 0) and not r.can_place(0, 1)
    r.place(1, 1)
    assert not r.can_place(1, 1) and r.is_occupied(1, 1)
    with pytest.raises(RuleViolation):
        r.place(1, 1)


def test_order_rule_refuses_to_seal_an_unbuilt_cell():
    # One-row corridor: building (2,0) would cut the depot off from (3,0), so the rule forbids it,
    # and (3,0) has no support yet. The compiler must report this blueprint as unbuildable.
    r = rs("D.##.\n")
    assert r.is_supported(2, 0) and not r.order_ok(2, 0) and not r.can_place(2, 0)
    assert not r.is_supported(3, 0) and not r.can_place(3, 0)
    with pytest.raises(UnbuildableError):
        r.check_buildable()


def test_same_corridor_with_a_second_row_is_fine():
    r = rs("D.##.\n.....\n")                          # row 2 keeps both cells reachable
    assert r.order_ok(2, 0) and r.can_place(2, 0)
    r.check_buildable(trials=10)


def test_shipped_blueprints_buildable_in_random_orders():
    for n in ("simple_wall", "wall_with_opening", "double_wall", "u_shape"):
        bp = load_blueprint(f"blueprints/{n}.json")
        ok, stuck = verify_buildable(RuleSet(bp).clone, trials=15, seed=1)
        assert ok, (n, stuck)


def test_every_target_reachable_when_complete():
    bp = load_blueprint("blueprints/u_shape.json")
    r = RuleSet(bp)
    while len(r.structure) < len(r.targets):
        c = next(c for c in sorted(r.targets - r.structure.cells) if r.can_place(*c))
        r.place(*c)
    assert r.structure.cells == set(bp.targets)


def test_module_level_functions_use_active_ruleset():
    r = rs("D....\n.###.\n")
    R.set_active(r)
    assert R.can_place(1, 1) and R.is_supported(1, 1) and R.order_ok(1, 1) and not R.is_occupied(1, 1)
