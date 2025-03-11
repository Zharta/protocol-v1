from textwrap import dedent

import boa
import pytest
from eth_account import Account


@pytest.fixture(scope="session", autouse=True)
def boa_env():
    boa.interpret.set_cache_dir(cache_dir=".cache/titanoboa")
    return boa


@pytest.fixture(scope="session")
def accounts():
    _accounts = [boa.env.generate_address() for _ in range(10)]
    for account in _accounts:
        boa.env.set_balance(account, 10**21)
    return _accounts


@pytest.fixture(scope="session")
def owner_account():
    return Account.create()


@pytest.fixture(scope="session")
def not_owner_account():
    return Account.create()


@pytest.fixture(scope="session", autouse=True)
def contract_owner(accounts, owner_account):
    boa.env.eoa = owner_account.address
    boa.env.set_balance(owner_account.address, 10**21)
    return owner_account.address


@pytest.fixture(scope="session")
def not_contract_owner(not_owner_account):
    return not_owner_account.address


@pytest.fixture(scope="session")
def investor(accounts):  # noqa: FURB118
    return accounts[1]


@pytest.fixture(scope="session")
def borrower(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def protocol_wallet(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def erc721_contract():
    return boa.load_partial("contracts/auxiliary/token/ERC721.vy")


@pytest.fixture(scope="session")
def weth9_contract():
    return boa.load_partial("contracts/auxiliary/token/WETH9Mock.vy")


@pytest.fixture(scope="session")
def cryptopunks_contract():
    return boa.load_partial("contracts/auxiliary/token/CryptoPunksMarketMock.vy")


@pytest.fixture(scope="session")
def delegation_registry_contract():
    return boa.load_partial("contracts/auxiliary/delegate/DelegationRegistryMock.vy")


@pytest.fixture(scope="session")
def genesis_contract():
    return boa.load_partial("contracts/GenesisPass.vy")


@pytest.fixture(scope="session")
def lendingpool_eth_otc_contract():
    return boa.load_partial("contracts/LendingPoolEthOTC.vy")


@pytest.fixture(scope="session")
def lendingpool_erc20_otc_contract():
    return boa.load_partial("contracts/LendingPoolERC20OTC.vy")


@pytest.fixture(scope="session")
def lendingpool_core_contract():
    return boa.load_partial("contracts/LendingPoolCore.vy")


@pytest.fixture(scope="session")
def lendingpool_lock_contract():
    return boa.load_partial("contracts/LendingPoolLock.vy")


@pytest.fixture(scope="session")
def collateral_vault_peripheral_contract():
    return boa.load_partial("contracts/CollateralVaultPeripheral.vy")


@pytest.fixture(scope="session")
def collateral_vault_core_contract():
    return boa.load_partial("contracts/CollateralVaultCoreV2.vy")


@pytest.fixture(scope="session")
def cryptopunks_vault_core_contract():
    return boa.load_partial("contracts/CryptoPunksVaultCore.vy")


@pytest.fixture(scope="session")
def collateral_vault_otc_contract():
    return boa.load_partial("contracts/CollateralVaultOTC.vy")


@pytest.fixture(scope="session")
def loans_core_contract():
    return boa.load_partial("contracts/LoansCore.vy")


@pytest.fixture(scope="session")
def loans_peripheral_contract():
    return boa.load_partial("contracts/Loans.vy")


@pytest.fixture(scope="session")
def loans_otc_contract():
    return boa.load_partial("contracts/LoansOTC.vy")


@pytest.fixture(scope="session")
def liquidations_otc_contract():
    return boa.load_partial("contracts/LiquidationsOTC.vy")


@pytest.fixture(scope="session")
def liquidations_core_contract():
    return boa.load_partial("contracts/LiquidationsCore.vy")


@pytest.fixture(scope="session")
def liquidations_peripheral_contract():
    return boa.load_partial("contracts/LiquidationsPeripheral.vy")


@pytest.fixture(scope="module")
def empty_contract():
    return boa.loads_partial(
        dedent("""
        dummy: uint256
     """)
    )


@pytest.fixture(scope="module")
def path_to_erc20_mock():
    # this is not required for loans core functionality, but is needed to find the erc20
    # to use in events.
    # TODO: consider remove the events dependency
    return boa.loads_partial(
        dedent("""

        @external
        @view
        def lendingPoolPeripheralContract() -> address:
            return self

        @external
        @view
        def erc20TokenContract() -> address:
            return self

     """)
    )
