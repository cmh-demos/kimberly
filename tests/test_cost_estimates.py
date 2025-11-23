import importlib.util
import os


def load_estimate():
    here = os.path.dirname(__file__)
    path = os.path.join(here, '..', 'scripts', 'cost_smoke_test.py')
    spec = importlib.util.spec_from_file_location('cost_smoke_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.estimate


def test_estimate_runs():
    # Smoke test: runs the estimator with free_mode True and ensures embedding cost is zero
    estimate = load_estimate()
    result = estimate(users=10, vectors_per_user=10, dim=256, use_float16=True, free_mode=True)
    assert result['embedding_cost'] == 0


if __name__ == '__main__':
    test_estimate_runs()
