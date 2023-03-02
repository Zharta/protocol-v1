from enum import Enum
from typing import Optional, Callable, Any
from ape_accounts.accounts import KeyfileAccount
from ape.contracts.base import ContractContainer, ContractInstance
from dataclasses import dataclass, field
from ape import project

Environment = Enum('Environment', ['local', 'dev', 'int', 'prod'])


class ContractConfig():
    pass


@dataclass
class DeploymentContext():

    contract: dict[str, ContractConfig]
    env: Environment
    owner: KeyfileAccount
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
    contract: Optional[ContractInstance]
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
        kwargs = {"sender": context.owner.address} | context.gas_options()
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"## {self.name} <- {self.container_name}.deploy({kwargs_str})")
        if not dryrun:
            self.contract = self.container.deploy(**kwargs)


class NFT(ExternalContract):

    def __init__(self, name: str, contract: Optional[ContractInstance]):
        super().__init__(name, contract, project.ERC721, nft=True, container_name="ERC721")


class Token(ExternalContract):

    _config_key: str

    def __init__(self, name: str, key: str, contract: Optional[ContractInstance]):
        super().__init__(name, contract, project.ERC20, nft=False, container_name="ERC20")
        self._config_key = key

    def config_key(self):
        return self._config_key

    def deploy(self, context: DeploymentContext, dryrun: bool = False):
        if self.contract is not None:
            print(f"WARNING: Deployment will override contract *{self.name}* at {self.contract}")
        if not self.deployable(context):
            raise Exception(f"Cant deploy contract {self} in current context")
        args = [self.name, self.name, 18, 10**30]
        kwargs = {"sender": context.owner.address} | context.gas_options()
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in args)}) [{self.name}]")
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in args)}, {kwargs_str}) [{self.name}]")
        if not dryrun:
            self.contract = self.container.deploy(*args, **kwargs)


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
        print_args = self.deployment_args_contracts
        kwargs = self.deployment_options(context)
        kwargs_str = ",".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"## {self.name} <- {self.container_name}.deploy({','.join(str(a) for a in print_args)}, {kwargs_str})")
        if not dryrun:
            self.contract = self.container.deploy(*self.deployment_args(context), **kwargs)
