.PHONY: venv install install-dev test run clean interfaces docs

VENV?=./.venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip

CONTRACTS := $(shell find contracts -depth 1 -name '*.vy')
NATSPEC := $(patsubst contracts/%, natspec/%, $(CONTRACTS:%.vy=%.json))
PATH := ${VENV}/bin:${PATH}

vpath %.vy ./contracts

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	${PIP} install -U pip
	${PIP} install wheel

install: ${VENV}
	${PIP} install -r requirements.txt
	${VENV}/bin/ape plugins install --upgrade .

install-dev: ${VENV}
	${PIP} install -r requirements-dev.txt

test: ${VENV}
	${VENV}/bin/pytest tests/unit --durations=0

coverage:
	${VENV}/bin/coverage run -m pytest tests/unit --durations=0
	${VENV}/bin/coverage report

unit-tests:
	${VENV}/bin/pytest tests/unit --durations=0 -n auto --dist loadscope

integration-tests:
	${VENV}/bin/pytest -n auto tests/integration --durations=0 --dist loadscope

stateful-tests:
	${VENV}/bin/pytest tests/stateful --durations=0 -n auto

gas:
	${VENV}/bin/pytest tests/integration --gas-profile


interfaces:
	${VENV}/bin/python scripts/build_interfaces.py contracts/*.vy

docs: $(NATSPEC)

natspec/%.json: %.vy
	${VENV}/bin/vyper -f userdoc,devdoc $< > $@

clean:
	rm -rf ${VENV} .cache


%-local: export ENV=local
%-dev: export ENV=dev
%-int: export ENV=int
%-prod: export ENV=prod

add-account:
	${VENV}/bin/ape accounts import $(alias)

compile:
	rm -rf .build/*
	${VENV}/bin/ape compile

console-local:
	${VENV}/bin/ape console --network ethereum:local:foundry

deploy-local: 
	${VENV}/bin/ape run -I deployment --network ethereum:local:foundry

console-dev:
	${VENV}/bin/ape console --network https://network.dev.zharta.io

deploy-dev:
	${VENV}/bin/ape run -I deployment --network https://network.dev.zharta.io

console-int:
	${VENV}/bin/ape console --network ethereum:sepolia:alchemy

deploy-int:
	${VENV}/bin/ape run -I deployment --network ethereum:sepolia:alchemy

console-prod:
	${VENV}/bin/ape console --network ethereum:mainnet:alchemy

deploy-prod: compile
	${VENV}/bin/ape run -I deployment --network ethereum:mainnet:alchemy
