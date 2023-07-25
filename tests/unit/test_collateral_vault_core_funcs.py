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
def collateral_vault_core(collateral_vault_core_contract, delegation_registry, contract_owner):
    with boa.env.prank(contract_owner):
        return collateral_vault_core_contract.deploy(delegation_registry)


@pytest.fixture(scope="module")
def erc721(erc721_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return erc721_contract.deploy()


def test_store_collateral_wrong_sender(collateral_vault_core, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_core.storeCollateral(contract_owner, ZERO_ADDRESS, 0, ZERO_ADDRESS, sender=contract_owner)


def test_store_collateral(collateral_vault_core, erc721, borrower, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(collateral_vault_core, 0, sender=borrower)

    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    collateral_vault_core.storeCollateral(borrower, erc721, 0, ZERO_ADDRESS, sender=collateral_vault_peripheral)

    assert erc721.ownerOf(0) == collateral_vault_core.address


def test_transfer_collateral_wrong_sender(collateral_vault_core, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_core.transferCollateral(contract_owner, ZERO_ADDRESS, 0, contract_owner, sender=contract_owner)


def test_transfer_collateral(collateral_vault_core, erc721, borrower, contract_owner):
    collateral_vault_peripheral = boa.env.generate_address()
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(collateral_vault_core, 0, sender=borrower)

    collateral_vault_core.setCollateralVaultPeripheralAddress(collateral_vault_peripheral, sender=contract_owner)

    collateral_vault_core.storeCollateral(borrower, erc721, 0, ZERO_ADDRESS, sender=collateral_vault_peripheral)

    assert erc721.ownerOf(0) == collateral_vault_core.address

    collateral_vault_core.transferCollateral(borrower, erc721, 0, borrower, sender=collateral_vault_peripheral)

    assert erc721.ownerOf(0) == borrower
