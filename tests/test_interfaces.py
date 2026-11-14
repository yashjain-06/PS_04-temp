from src.sim.fake_model import FakeModel
from src.utils.interface_check import check_model, check_modules


def test_fake_model_satisfies_model_contract():
    res = check_model(FakeModel(blueprint="blueprints/wall_with_opening.json", n_agents=10, seed=1))
    hard = [r for r in res if not r[1] and r[0] != "one robot per cell"]
    assert not hard, hard


def test_module_check_reports_missing_functions_instead_of_crashing():
    res = check_modules()
    assert res and all(len(r) == 3 for r in res)
    assert any(name == "src.sim.failure.fail_agents" and ok for name, ok, _ in res)
