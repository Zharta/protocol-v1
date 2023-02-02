from enum import Enum
from typing import Optional, Callable, Any
from brownie.network.account import Account
from brownie.network.contract import ContractContainer, ProjectContract
from brownie import ERC721, ERC20
from dataclasses import dataclass, field

Environment = Enum('Environment', ['local', 'dev', 'int', 'prod'])


class ContractConfig():
    pass


@dataclass
class DeploymentContext():

    contract: dict[str, ContractConfig]
    env: Environment
    owner: Account
    config: dict[str, Any] = field(default_factory=dict)
    gas_func: Callable = None

    def __getitem__(self, key):
        return self.contract[key] if key in self.contract else self.config[key]

    def keys(self):
        return self.contract.keys() | self.config.keys()

    def gas_options(self):
        return self.gas_func(self) if self.gas_func is not None else {}


@dataclass
class ContractConfig():

    name: str
    contract: Optional[ProjectContract]
    container: ContractContainer
    nft: bool = False
    container_name: str = None
    deployment_deps: set[str] = field(default_factory=set)
    config_deps: dict[str, Callable] = field(default_factory=dict)

    def deployable(self, context: DeploymentContext) -> bool:
        return False

    def deployment_dependencies(self) -> set[str]:
        return self.deployment_deps

    def config_dependencies(self) -> dict[str, Callable]:
        return self.config_deps

    def deploy(self, context: DeploymentContext, dryrun: bool = False) -> ContractConfig:
        pass

    def config_dependency(self, contract: ContractConfig, context: DeploymentContext, dryrun: bool = False):
        pass

    def address(self):
        return self.contract.address if self.contract else None

    def config_key(self):
        return self.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Contract[name={self.name}, nft={self.nft}, contract={self.contract}, container_name={self.container_name}]"


@dataclass
class ExternalContract(ContractConfig):

    def deployable(self, context: DeploymentContext) -> bool:
        return context.env != Environment.prod

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        args = [{'from': context.owner.address} | context.gas_options()]
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in args)})")
        if not dryrun:
            self.contract = self.container.deploy(*args)


class NFT(ExternalContract):

    config_order: int

    def __init__(self, name: str, contract: Optional[ProjectContract], config_order=0):
        super().__init__(name, contract, ERC721, nft=True, container_name="ERC721")
        self.config_order = config_order


class Token(ExternalContract):

    _config_key: str

    def __init__(self, name: str, key: str, contract: Optional[ProjectContract]):
        super().__init__(name, contract, ERC20, nft=False, container_name="ERC20")
        self._config_key = key

    def config_key(self):
        return self._config_key

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        args = [self.name, self.name, 18, 10**30, {'from': context.owner.address} | context.gas_options()]
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in args)}) [{self.name}]")
        if not dryrun:
            self.contract = self.container.deploy(*args)


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
        return {'from': context.owner.address} | context.gas_options()

    def deployable(self, contract: DeploymentContext) -> bool:
        return True

    def deploy(self, context: DeploymentContext, dryrun: bool = False) -> ContractConfig:
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        print_args = [*self.deployment_args_contracts, self.deployment_options(context)]
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in print_args)}")
        args = [*self.deployment_args(context), self.deployment_options(context)]
        if not dryrun:
            self.contract = self.container.deploy(*args)
