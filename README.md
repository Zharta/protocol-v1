# Zharta Smart Contracts for Ethereum

This repository contains Zharta's smart contracts to run in Ethereum. It also contains the automatic tests that validate their quality. The smart contracts are written using [Vyper](https://vyper.readthedocs.io/en/stable/toctree.html) and the tests use [Brownie](https://eth-brownie.readthedocs.io/en/stable/toctree.html).

## Running the tests

To run the tests locally, install Brownie (see [here](https://eth-brownie.readthedocs.io/en/stable/install.html)) and Ganache-CLI (see [here](https://www.npmjs.com/package/ganache-cli)). In the root of the project, run
```bash
$ brownie test
```

## Interacting with the contracts locally

To interact and test the smart contracts manually in a local machine, start a Brownie console. It will automatically start `ganache-cli` for you:
```
$ brownie console
```

Using the console, the smart contracts can be deployed and tests manually. For example, deploying the `Loans.vy` smart contract and checking the owner can be done by:
```
>>> loans_contract = Loans.deploy({"from": accounts[0]})
>>> loans_contract.owner()
```

To see more about interacting with smart contracts using Brownie, check [here](https://eth-brownie.readthedocs.io/en/stable/core-contracts.html).





