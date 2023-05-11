.PHONY: venv install install-dev test run clean interfaces docs

VENV?=./.venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip

CONTRACTS := $(shell find contracts -depth 1 -name '*.vy')
NATSPEC := $(patsubst contracts/%, natspec/%, $(CONTRACTS:%.vy=%.json))

vpath %.vy ./contracts

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	${PIP} install -U pip
	${PIP} install wheel

install: ${VENV}
	${PIP} install -r requirements.txt

install-dev: ${VENV}
	${PIP} install -r requirements-dev.txt

test: ${VENV}
	${VENV}/bin/pytest tests --durations=0 --profile

interfaces:
	python scripts/build_interfaces.py contracts/*.vy

docs: $(NATSPEC)

natspec/%.json: %.vy
	vyper -f userdoc,devdoc $< > $@

clean:
	rm -rf ${VENV} .cache
