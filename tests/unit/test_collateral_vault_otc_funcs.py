import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module")
def contract_owner():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def loans_peripheral():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def liquidations():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc721(erc721_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return erc721_contract.deploy()


@pytest.fixture(scope="module")
def erc20_token(weth9_contract, contract_owner):
    with boa.env.prank(contract_owner):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def cryptopunks(cryptopunks_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return cryptopunks_contract.deploy()


@pytest.fixture(scope="module")
def delegation_registry(delegation_registry_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return delegation_registry_contract.deploy()


@pytest.fixture(scope="module")
def collateral_vault_otc(
    collateral_vault_otc_contract,
    contract_owner,
    delegation_registry,
    cryptopunks,
    loans_peripheral,
    liquidations,
    erc20_token,
):
    with boa.env.prank(contract_owner):
        contract = collateral_vault_otc_contract.deploy(cryptopunks, delegation_registry)
        proxy_address = contract.create_proxy()
        proxy = collateral_vault_otc_contract.at(proxy_address)
        proxy.setLoansAddress(loans_peripheral)
        proxy.setLiquidationsPeripheralAddress(liquidations)
        return proxy


def test_store_collateral_zero_values(collateral_vault_otc, erc721, borrower, loans_peripheral):
    with boa.env.prank(loans_peripheral):
        with boa.reverts("address is the zero addr"):
            collateral_vault_otc.storeCollateral(
                ZERO_ADDRESS,
                ZERO_ADDRESS,
                0,
                ZERO_ADDRESS,
                False,
            )

        with boa.reverts("collat addr is the zero addr"):
            collateral_vault_otc.storeCollateral(
                borrower,
                ZERO_ADDRESS,
                0,
                ZERO_ADDRESS,
                False,
            )

        with boa.reverts("address is the zero addr"):
            collateral_vault_otc.storeCollateral(
                borrower,
                erc721,
                0,
                ZERO_ADDRESS,
                False,
            )


def test_store_collateral_wrong_sender(collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc.storeCollateral(
            borrower,
            erc721,
            0,
            erc20_token,
            False,
        )


def test_store_collateral_not_nft_contract(collateral_vault_otc, loans_peripheral, erc20_token, borrower, contract_owner):
    with boa.reverts():
        collateral_vault_otc.storeCollateral(borrower, erc20_token, 0, erc20_token, False, sender=loans_peripheral)


def test_store_collateral_wrong_owner(collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner):
    erc721.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by wallet"):
        collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20_token, False, sender=loans_peripheral)


def test_store_collateral_not_approved(collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner):
    erc721.mint(borrower, 0, sender=contract_owner)

    with boa.reverts("transfer is not approved"):
        collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20_token, False, sender=loans_peripheral)


def test_store_collateral(collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner):
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(collateral_vault_otc, 0, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20_token, False, sender=loans_peripheral)
    event = get_last_event(collateral_vault_otc, name="CollateralStored")

    assert erc721.ownerOf(0) == collateral_vault_otc.address

    assert event.collateralAddress == erc721.address
    assert event.tokenId == 0
    assert event._from == borrower


def test_store_cryptopunk_collateral(
    collateral_vault_otc, loans_peripheral, cryptopunks, erc20_token, borrower, contract_owner
):
    cryptopunks.mint(borrower, 0, sender=contract_owner)
    cryptopunks.offerPunkForSaleToAddress(0, 0, collateral_vault_otc, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, cryptopunks, 0, erc20_token, False, sender=loans_peripheral)
    event = get_last_event(collateral_vault_otc, name="CollateralStored")

    assert cryptopunks.punkIndexToAddress(0) == collateral_vault_otc.address

    assert event.collateralAddress == cryptopunks.address
    assert event.tokenId == 0
    assert event._from == borrower

    cryptopunks.transferPunk(borrower, 0, sender=collateral_vault_otc.address)


def test_transfer_collateral_from_loan_zero_values(collateral_vault_otc, erc721, borrower):
    with boa.reverts("address is the zero addr"):
        collateral_vault_otc.transferCollateralFromLoan(ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS)

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_otc.transferCollateralFromLoan(borrower, ZERO_ADDRESS, 0, ZERO_ADDRESS)

    with boa.reverts("address is the zero addr"):
        collateral_vault_otc.transferCollateralFromLoan(borrower, erc721, 0, ZERO_ADDRESS)


def test_transfer_collateral_from_loan_wrong_sender(
    collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner
):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc.transferCollateralFromLoan(borrower, erc721, 0, erc20_token)


def test_transfer_collateral_from_loan_not_nft_contract(
    collateral_vault_otc, loans_peripheral, erc20_token, borrower, contract_owner
):
    with boa.reverts():
        collateral_vault_otc.transferCollateralFromLoan(borrower, erc20_token, 0, erc20_token, sender=loans_peripheral)


def test_transfer_collateral_from_loan_wrong_owner(
    collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner
):
    erc721.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by vault"):
        collateral_vault_otc.transferCollateralFromLoan(borrower, erc721, 0, erc20_token, sender=loans_peripheral)


def test_transfer_collateral_from_loan(collateral_vault_otc, loans_peripheral, erc721, erc20_token, borrower, contract_owner):
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(collateral_vault_otc, 0, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20_token, False, sender=loans_peripheral)

    assert erc721.ownerOf(0) == collateral_vault_otc.address

    collateral_vault_otc.transferCollateralFromLoan(borrower, erc721, 0, erc20_token, sender=loans_peripheral)
    event = get_last_event(collateral_vault_otc, name="CollateralFromLoanTransferred")

    assert erc721.ownerOf(0) == borrower

    assert event.collateralAddress == erc721.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_cryptopunk_collateral_from_loan(
    collateral_vault_otc, loans_peripheral, cryptopunks, erc20_token, borrower, contract_owner
):
    cryptopunks.mint(borrower, 0, sender=contract_owner)
    cryptopunks.offerPunkForSaleToAddress(0, 0, collateral_vault_otc, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, cryptopunks, 0, erc20_token, False, sender=loans_peripheral)

    assert cryptopunks.punkIndexToAddress(0) == collateral_vault_otc.address

    collateral_vault_otc.transferCollateralFromLoan(borrower, cryptopunks, 0, erc20_token, sender=loans_peripheral)
    event = get_last_event(collateral_vault_otc, name="CollateralFromLoanTransferred")

    assert cryptopunks.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_collateral_from_liquidation_wrong_sender(collateral_vault_otc):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc.transferCollateralFromLiquidation(ZERO_ADDRESS, ZERO_ADDRESS, 0)


def test_transfer_collateral_from_liquidation_zero_values(collateral_vault_otc, liquidations, borrower, contract_owner):
    with boa.reverts("address is the zero addr"):
        collateral_vault_otc.transferCollateralFromLiquidation(ZERO_ADDRESS, ZERO_ADDRESS, 0, sender=liquidations)

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_otc.transferCollateralFromLiquidation(borrower, ZERO_ADDRESS, 0, sender=liquidations)


def test_transfer_collateral_from_liquidation_not_nft_contract(
    collateral_vault_otc, liquidations, erc20_token, borrower, contract_owner
):
    with boa.reverts():
        collateral_vault_otc.transferCollateralFromLiquidation(borrower, erc20_token, 0, sender=liquidations)


def test_transfer_collateral_from_liquidation_wrong_owner(
    collateral_vault_otc, liquidations, erc721, borrower, contract_owner
):
    erc721.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by vault"):
        collateral_vault_otc.transferCollateralFromLiquidation(borrower, erc721, 0, sender=liquidations)


def test_transfer_collateral_from_liquidation(
    collateral_vault_otc, loans_peripheral, liquidations, erc721, erc20_token, borrower, contract_owner
):
    erc721.mint(borrower, 0, sender=contract_owner)
    erc721.approve(collateral_vault_otc, 0, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, erc721, 0, erc20_token, False, sender=loans_peripheral)

    assert erc721.ownerOf(0) == collateral_vault_otc.address

    collateral_vault_otc.transferCollateralFromLiquidation(borrower, erc721, 0, sender=liquidations)
    event = get_last_event(collateral_vault_otc, name="CollateralFromLiquidationTransferred")

    assert erc721.ownerOf(0) == borrower

    assert event.collateralAddress == erc721.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_collateral_from_liquidation(
    collateral_vault_otc, loans_peripheral, liquidations, cryptopunks, erc20_token, borrower, contract_owner
):
    cryptopunks.mint(borrower, 0, sender=contract_owner)
    cryptopunks.offerPunkForSaleToAddress(0, 0, collateral_vault_otc, sender=borrower)

    collateral_vault_otc.storeCollateral(borrower, cryptopunks, 0, erc20_token, False, sender=loans_peripheral)

    assert cryptopunks.punkIndexToAddress(0) == collateral_vault_otc.address

    collateral_vault_otc.transferCollateralFromLiquidation(borrower, cryptopunks, 0, sender=liquidations)
    event = get_last_event(collateral_vault_otc, name="CollateralFromLiquidationTransferred")

    assert cryptopunks.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks.address
    assert event.tokenId == 0
    assert event._to == borrower
