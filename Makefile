.PHONY: venv install install-dev test run clean interfaces docs

VENV?=./.venv
PYTHON=${VENV}/bin/python3
PIP=${VENV}/bin/pip

CONTRACTS := $(shell find contracts -depth 1 -name '*.vy')
NATSPEC := $(patsubst contracts/%, natspec/%, $(CONTRACTS:%.vy=%.json))

vpath %.vy ./contracts

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	${PIP} install -U pip
	${PIP} install wheel

venv: ${VENV}/bin/activate

install: venv
	${PIP} install -r requirements.txt

install-dev: venv install
	${PIP} install -r requirements-dev.txt

test: venv install-dev
	patch contracts/LiquidationsPeripheral.vy tests/nftx_workaround.patch
	${VENV}/bin/brownie test ; patch -R contracts/LiquidationsPeripheral.vy tests/nftx_workaround.patch

full-test: venv install-dev
	${VENV}/bin/brownie test --durations=20 --gas --network ganache-mainnet-fork

interfaces:
	python scripts/build_interfaces.py contracts/*.vy

docs: $(NATSPEC)

natspec/%.json: %.vy
	vyper -f userdoc,devdoc $< > $@

clean:
	rm -rf ${VENV}
