.PHONY: test
test:
	pytest

.PHONY: install
install:
	python setup.py bdist_wheel
	pip install --upgrade dist/eepromer-0.1-py3-none-any.whl
