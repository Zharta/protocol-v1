import json
import logging
import os
import warnings
from pathlib import Path
from typing import Any

from ape import accounts

from . import contracts as contracts_module
from .basetypes import (
    ContractConfig,
    DeploymentContext,
    Environment,
)
from .dependency import DependencyManager

ENV = Environment[os.environ.get("ENV", "local")]


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
warnings.filterwarnings("ignore")


def load_contracts(env: Environment, chain: str) -> list[ContractConfig]:
    config_file = Path.cwd() / "configs" / env.name / chain / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    contract_configs = {
        f"{pool_id.lower()}.{key}": c for pool_id, pool in config["pools"].items() for key, c in pool["contracts"].items()
    } | {f"common.{k}": v for k, v in config["common"].items()}

    return [
        contracts_module.__dict__[c["contract_def"]](
            key=key, address=c.get("contract"), abi_key=c.get("abi_key"), **c.get("properties", {})
        )
        for key, c in contract_configs.items()
    ]


def store_contracts(env: Environment, chain: str, contracts: list[ContractConfig]):
    config_file = Path.cwd() / "configs" / env.name / chain / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    contracts_dict = {c.key: c for c in contracts}

    contract_configs = {
        f"{pool_id.lower()}.{key}": c for pool_id, pool in config["pools"].items() for key, c in pool["contracts"].items()
    } | {f"common.{k}": v for k, v in config["common"].items()}

    for key, c in contract_configs.items():
        if key in contracts_dict:
            c["contract"] = contracts_dict[key].address()
            if contracts_dict[key].abi_key:
                c["abi_key"] = contracts_dict[key].abi_key
            if contracts_dict[key].version:
                c["version"] = contracts_dict[key].version

    with config_file.open(mode="w", encoding="utf8") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))


def load_nft_contracts(env: Environment, chain: str) -> list[ContractConfig]:
    config_file = Path.cwd() / "configs" / env.name / chain / "collections.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    return [
        contracts_module.__dict__[c.get("contract_def", "ERC721")](
            key=key,
            address=c.get("contract_address"),
            abi_key=c.get("abi_key"),
        )
        for key, c in config.items()
    ]


def load_tokens(env: Environment, chain: str) -> list[ContractConfig]:
    config_file = Path.cwd() / "configs" / env.name / chain / "tokens.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    return [
        contracts_module.__dict__[c.get("contract_def", "ERC20External")](key=f"common.{name}", address=c.get("address"))
        for name, c in config.items()
    ]


def load_configs(env: Environment, chain: str) -> dict:
    config_file = Path.cwd() / "configs" / env.name / chain / "pools.json"
    with config_file.open(encoding="utf8") as f:
        config = json.load(f)

    _configs = config.get("configs", {})
    return {f"configs.{k}": v for k, v in _configs.items()}


class DeploymentManager:
    def __init__(self, env: Environment, chain: str):
        self.env = env
        self.chain = chain
        match env:
            case Environment.local:
                self.owner = accounts[0]
            case Environment.dev:
                self.owner = accounts.load("devacc")
            case Environment.int:
                self.owner = accounts.load("intacc")
            case Environment.prod:
                self.owner = accounts.load("prodacc")
        self.context = DeploymentContext(self._get_contracts(), self.env, self.chain, self.owner, self._get_configs())

    def _get_contracts(self) -> dict[str, ContractConfig]:
        contracts = load_contracts(self.env, self.chain)
        nfts = load_nft_contracts(self.env, self.chain)
        tokens = load_tokens(self.env, self.chain)
        all_contracts = contracts + nfts + tokens

        # always deploy everything in local
        if self.env == Environment.local:
            for contract in all_contracts:
                contract.contract = None

        return {c.key: c for c in all_contracts}

    def _get_configs(self) -> dict[str, Any]:
        return load_configs(self.env, self.chain)

    def _save_state(self):
        contracts = [c for c in self.context.contracts.values() if not c.nft and not c.token]
        store_contracts(self.env, self.chain, contracts)

    def deploy(self, changes: set[str], *, dryrun=False, save_state=True):
        self.owner.set_autosign(True)
        self.context.dryrun = dryrun
        dependency_manager = DependencyManager(self.context, changes)
        contracts_to_deploy = dependency_manager.build_contract_deploy_set()
        dependencies_tx = dependency_manager.build_transaction_set()

        for contract in contracts_to_deploy:
            if contract.deployable(self.context):
                contract.deploy(self.context)

        if save_state and not dryrun:
            self._save_state()

        for dependency_tx in dependencies_tx:
            dependency_tx(self.context)

        if save_state and not dryrun:
            self._save_state()

    def deploy_all(self, *, dryrun=False, save_state=True):
        self.deploy(self.context.contract.keys(), dryrun=dryrun, save_state=save_state)
