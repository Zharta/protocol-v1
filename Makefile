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
	ape plugins install --upgrade .

install-dev: ${VENV}
	${PIP} install -r requirements-dev.txt

test: ${VENV}
	rm -rf .cache/
	${VENV}/bin/pytest -n auto tests --durations=0

gas:
	${VENV}/bin/pytest tests --durations=0 --profile
	

interfaces:
	python scripts/build_interfaces.py contracts/*.vy

docs: $(NATSPEC)

natspec/%.json: %.vy
	vyper -f userdoc,devdoc $< > $@

clean:
	rm -rf ${VENV} .cache


%-local: export ENV=local
%-dev: export ENV=dev
%-int: export ENV=int
%-prod: export ENV=prod

console-local:
	ape console --network ethereum:local:ganache

deploy-local:
	ape run -I deployment --network ethereum:local:ganache

console-dev:
	ape console --network https://network.dev.zharta.io

deploy-dev:
	ape run -I deployment --network https://network.dev.zharta.io

console-int:
	ape console --network ethereum:sepolia:alchemy

deploy-int:
	ape run -I deployment --network ethereum:sepolia:alchemy

console-prod:
	ape console --network ethereum:mainnet:alchemy

deploy-prod:
	ape run -I deployment --network ethereum:mainnet:alchemy
