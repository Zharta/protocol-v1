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

install: $(VENV)
	${PIP} install -r requirements.txt

install-dev: $(VENV) install
	${PIP} install -r requirements-dev.txt

test: export FORK=false
test: $(VENV) install-dev
	patch contracts/LiquidationsPeripheral.vy tests/nftx_workaround.patch
	${VENV}/bin/brownie test ; patch -R contracts/LiquidationsPeripheral.vy tests/nftx_workaround.patch

full-test: $(VENV) install-dev
	${VENV}/bin/brownie test --durations=20 --gas --network ganache-mainnet-fork

interfaces:
	python scripts/build_interfaces.py -o contracts/interfaces contracts/*.vy

docs: $(NATSPEC)

natspec/%.json: %.vy
	vyper -f userdoc,devdoc $< > $@

clean:
	rm -rf ${VENV}
