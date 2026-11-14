.PHONY: install test run experiments media surrogate check
install:
	pip install -r requirements.txt
test:
	pytest -q && node tests/charts_helpers.test.js
run:
	python scripts/run_server.py
experiments:
	python scripts/run_all_experiments.py
media: experiments
	python scripts/make_gif.py
surrogate:
	python scripts/make_surrogate_data.py && python scripts/train_surrogate.py
check:
	python scripts/check_interfaces.py
