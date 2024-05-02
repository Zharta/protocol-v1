import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Any

from ape import project
from ape.contracts.base import ContractContainer, ContractInstance
from ape_accounts.accounts import KeyfileAccount

Environment = Enum("Environment", ["local", "dev", "int", "prod"])


def abi_key(abi: list) -> str:
    json_dump = json.dumps(abi, sort_keys=True)
    _hash = hashlib.sha1(json_dump.encode("utf8"))
    return _hash.hexdigest()


@dataclass
class DeploymentContext:
    contract: dict[str, Any]
    env: Environment
    owner: KeyfileAccount
    pools: list[str]
    config: dict[str, Any] = field(default_factory=dict)
    gas_func: Callable | None = None
    dryrun: bool = False

    def __getitem__(self, key):
        if key in self.contract:
            return self.contract[key]
        if key in self.config:
            return self.config[key]
        return self.pool_contract[key]

    def keys(self):
        return self.contract.keys() | self.config.keys()

    def gas_options(self):
        return self.gas_func(self) if self.gas_func is not None else {}

    @cached_property
    def pool_contract(self):
        return {(pool, c.name): k for k, c in self.contract.items() for pool in (c.pools or [])}


@dataclass
class ContractConfig:
    key: str
    contract: ContractInstance | None
    container: ContractContainer
    container_name: str | None = None
    deployment_deps: set[str] = field(default_factory=set)
    config_deps: dict[str, Callable] = field(default_factory=dict)
    deployment_args: list[Any] = field(default_factory=list)
    abi_key: str | None = None
    version: str | None = None

    nft: bool = False

    def deployable(self, context: DeploymentContext) -> bool:  # noqa: PLR6301, ARG002
        return True

    def deployment_dependencies(self, context: DeploymentContext) -> set[str]:  # noqa: ARG002
        return self.deployment_deps

    def deployment_args_values(self, context: DeploymentContext) -> list[Any]:
        values = [context.get(c, c) for c in self.deployment_args]
        return [v.contract if isinstance(v, ContractConfig) else v for v in values]

    def deployment_args_repr(self, context: DeploymentContext) -> list[Any]:
        return [f"[{c}]" if c in context else c for c in self.deployment_args]

    def deployment_options(self, context: DeploymentContext) -> dict[str, Any]:  # noqa: PLR6301
        return {"sender": context.owner} | context.gas_options()

    # def config_dependency(self, contract: ContractConfig, context: DeploymentContext, dryrun: bool = False):
    #     pass

    def config_dependencies(self, context: DeploymentContext) -> dict[str, Callable]:  # noqa: ARG002
        return self.config_deps

    def address(self):
        return self.contract.address if self.contract else None

    def config_key(self):
        return self.key

    def __str__(self):
        return self.key

    def __repr__(self):
        return f"Contract[key={self.key}, contract={self.contract}, container_name={self.container_name}]"

    def load_contract(self, address: str):
        self.contract = self.container.at(address)

    def deploy(self, context: DeploymentContext):
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.key}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        print_args = self.deployment_args_repr(context)
        kwargs = self.deployment_options(context)
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"## {self.key} <- {self.container_name}.deploy({','.join(str(a) for a in print_args)}, {kwargs_str})")
        if not context.dryrun:
            self.contract = self.container.deploy(*self.deployment_args_values(context), **kwargs)
            self.abi_key = abi_key(self.contract.contract_type.dict()["abi"])


@dataclass
class ExternalContract(ContractConfig):
    def deployable(self, context: DeploymentContext) -> bool:
        return context.env != Environment.prod

    def deploy(self, context: DeploymentContext):
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        kwargs = {"sender": context.owner} | context.gas_options()
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"## {self.name} <- {self.container_name}.deploy({kwargs_str})")
        if not context.dryrun:
            self.contract = self.container.deploy(**kwargs)


class NFT(ExternalContract):
    def __init__(self, name: str, contract: ContractInstance | None):
        super().__init__(name, contract, project.ERC721, nft=True, container_name="ERC721")


class GenericExternalContract(ExternalContract):
    _address: str

    def __init__(self, name: str, address: str):
        super().__init__(name, None, None)
        self._address = address

    def address(self):
        return self._address

    def deployable(self, contract: DeploymentContext) -> bool:
        return False

    def __repr__(self):
        return f"GenericExternalContract[name={self.name}, address={self._address}]"


@dataclass
class InternalContract(ContractConfig):
    deployment_args_contracts: list[Any] = field(default_factory=list)

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context[c].contract for c in self.deployment_args_contracts]

    def deployment_options(self, context: DeploymentContext) -> dict[str, Any]:
        return {"sender": context.owner} | context.gas_options()

    def deployable(self, contract: DeploymentContext) -> bool:
        return True

    def deploy(self, context: DeploymentContext) -> ContractConfig:
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        print_args = self.deployment_args_contracts
        kwargs = self.deployment_options(context)
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(
            f"## {self.pools} {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in print_args)}, {kwargs_str})"
        )
        if not context.dryrun:
            self.contract = self.container.deploy(*self.deployment_args(context), **kwargs)


@dataclass
class MinimalProxy(InternalContract):
    impl: str = ""
    factory_func: str = "create_proxy"

    def deploy(self, context: DeploymentContext) -> ContractConfig:
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")

        impl_contract = context[self.impl].contract
        print_args = self.deployment_args_contracts
        kwargs = self.deployment_options(context)
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(
            f"## {self.pools} {self.name} <- {self.impl}.invoke_transaction({self.factory_func}, {','.join(str(a) for a in print_args)}, {kwargs_str})"
        )
        if not context.dryrun:
            tx = impl_contract.invoke_transaction(self.factory_func, *self.deployment_args(context), **kwargs)
            self.contract = self.container.at(tx.return_value)
