import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module", autouse=True)
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def delegation_registry(delegation_registry_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return delegation_registry_contract.deploy()


@pytest.fixture(scope="module")
def cryptopunks_market(cryptopunks_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return cryptopunks_contract.deploy()


@pytest.fixture(scope="module")
def cryptopunks_vault_core(cryptopunks_vault_core_contract, delegation_registry, cryptopunks_market, contract_owner):
    with boa.env.prank(contract_owner):
        return cryptopunks_vault_core_contract.deploy(cryptopunks_market, delegation_registry)


@pytest.fixture(scope="module")
def erc721(erc721_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return erc721_contract.deploy()


def test_store_collateral_wrong_sender(cryptopunks_vault_core, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core.storeCollateral(contract_owner, ZERO_ADDRESS, 0, ZERO_ADDRESS, sender=contract_owner)


def test_store_collateral_invalid(cryptopunks_vault_core, erc721, borrower, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(cryptopunks_vault_core, 0, sender=borrower)

    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    with boa.reverts("address not supported by vault"):
        cryptopunks_vault_core.storeCollateral(
            contract_owner, ZERO_ADDRESS, 0, ZERO_ADDRESS, sender=collateral_vault_peripheral
        )


def test_store_collateral(cryptopunks_vault_core, cryptopunks_market, contract_owner, borrower):
    collateral_vault_peripheral = boa.env.generate_address()
    cryptopunks_market.mint(borrower, 0, sender=contract_owner)
    cryptopunks_market.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core.address, sender=borrower)
    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    cryptopunks_vault_core.storeCollateral(borrower, cryptopunks_market, 0, ZERO_ADDRESS, sender=collateral_vault_peripheral)

    assert cryptopunks_market.punkIndexToAddress(0) == cryptopunks_vault_core.address
    cryptopunks_market.transferPunk(borrower, 0, sender=cryptopunks_vault_core.address)


def test_transfer_collateral_wrong_sender(cryptopunks_vault_core, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        cryptopunks_vault_core.transferCollateral(contract_owner, ZERO_ADDRESS, 0, contract_owner, sender=contract_owner)


def test_transfer_collateral(cryptopunks_vault_core, cryptopunks_market, contract_owner, borrower):
    collateral_vault_peripheral = boa.env.generate_address()
    cryptopunks_market.mint(borrower, 0, sender=contract_owner)
    cryptopunks_market.offerPunkForSaleToAddress(0, 0, cryptopunks_vault_core.address, sender=borrower)
    cryptopunks_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    cryptopunks_vault_core.storeCollateral(borrower, cryptopunks_market, 0, ZERO_ADDRESS, sender=collateral_vault_peripheral)
    assert cryptopunks_market.punkIndexToAddress(0) == cryptopunks_vault_core.address

    cryptopunks_vault_core.transferCollateral(borrower, cryptopunks_market, 0, borrower, sender=collateral_vault_peripheral)
    assert cryptopunks_market.punkIndexToAddress(0) == borrower
