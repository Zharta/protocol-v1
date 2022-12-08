from enum import Enum
from typing import Optional, Callable, Any
from brownie.network.account import Account
from brownie.network.contract import ContractContainer, ProjectContract
from brownie import ERC721, ERC20
from transactions import execute
from dataclasses import dataclass

Environment = Enum('Environment', ['local', 'dev', 'int', 'prod'])


class ContractConfig():
    pass


@dataclass
class DeploymentContext():

    contracts: dict[str, ContractConfig]
    env: Environment
    owner: Account
    # TODO gas_strategy?


@dataclass
class ContractConfig():

    name: str
    contract: Optional[ProjectContract]
    container: ContractContainer
    nft: bool = False
    container_name: str = None
    deployment_deps: set[str] = set()
    config_deps: dict[str, Callable] = dict()

    def deployable(self, contract: DeploymentContext) -> bool:
        pass

    def deployment_dependencies(self) -> set[str]:
        return self.deployment_deps

    def config_dependencies(self) -> dict[str, Callable]:
        return self.config_deps

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        pass

    def config_dependency(self, contract: ContractConfig, context: DeploymentContext, dryrun: bool = False):
        pass

    def address(self):
        return self.contract.address if self.contract else None

    def config_key(self):
        return self.name

    def __str__(self):
        return f"Contract[name={self.name}, nft={self.nft}, contract={self.contract}, container_name={self.container_name}]"


@dataclass
class ExternalContract(ContractConfig):

    def deployable(self, context: DeploymentContext) -> bool:
        return context.env != Environment.prod

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        if self.contract is not None:
            print(f"{self.name}: WARNING Deployment will override contract at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        _new = execute(self.container.deploy, {'from': {context.owner}}, _dryrun=dryrun)
        if not dryrun:
            self.contract = _new


class NFT(ExternalContract):

    config_order: int

    def __init__(self, name: str, contract: Optional[ProjectContract], config_order=0):
        super().__init__(name, contract, ERC721, nft=True, container_name="ERC721")
        self.config_order = config_order


class Token(ExternalContract):

    def __init__(self, name: str, key: str, contract: Optional[ProjectContract]):
        super().__init__(name, contract, ERC20, nft=False, container_name="ERC20")

    def config_key(self):
        return self.config_key


class GenericExternalContract(ExternalContract):

    address: str

    def __init__(self, name: str, address: str):
        super().__init__(name, None, None)
        self.address = address

    def address(self):
        return self.address

    def __str__(self):
        return f"GenericExternalContract[name={self.name}, address={self.address}]"


@dataclass
class InternalContract(ContractConfig):

    deployment_args_contracts: list[Any] = list()

    def deployment_args(self, context: DeploymentContext) -> list[Any]:
        return [context.contracts[c] for c in self.deployment_args_contracts]

    def deployment_options(self, context: DeploymentContext) -> dict[str, Any]:
        return {'from': context.owner}

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        if self.contract is not None:
            print(f"{self.name}: WARNING Deployment will override contract at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        _new = execute(
            self.container.deploy,
            *self.deployment_args(context),
            dry_run=dryrun,
            **self.deployment_options(context)
        )
        if not dryrun:
            self.contract = _new
