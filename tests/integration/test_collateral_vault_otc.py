import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event


@pytest.fixture(scope="module")
def liquidations_otc_contract(erc20_contract, liquidations_otc_contract_def, contract_owner):
    with boa.env.prank(contract_owner):
        contract = liquidations_otc_contract_def.deploy(erc20_contract)
        proxy_address = contract.create_proxy(50)
        return liquidations_otc_contract_def.at(proxy_address)


@pytest.fixture(scope="module")
def lendingpool_otc_contract(erc20_contract, lending_pool_eth_otc_contract_def, contract_owner, investor, protocol_wallet):
    with boa.env.prank(contract_owner):
        contract = lending_pool_eth_otc_contract_def.deploy(erc20_contract)
        proxy_address = contract.create_proxy(protocol_wallet, 250, investor)
        return lending_pool_eth_otc_contract_def.at(proxy_address)


@pytest.fixture(scope="module")
def collateral_vault_otc_contract(
    collateral_vault_otc_contract_def,
    cryptopunks_market_contract,
    delegation_registry_contract,
    contract_owner
):
    with boa.env.prank(contract_owner):
        contract = collateral_vault_otc_contract_def.deploy(cryptopunks_market_contract, delegation_registry_contract)
        proxy_address = contract.create_proxy()
        return collateral_vault_otc_contract_def.at(proxy_address)


@pytest.fixture(scope="module", autouse=True)
def setup(
    contracts_config,
    lendingpool_otc_contract,
    liquidations_otc_contract,
    erc20_contract,
    loans_core_contract,
    loans_peripheral_contract,
    collateral_vault_otc_contract,
    contract_owner,
):
    with boa.env.prank(contract_owner):
        lendingpool_otc_contract.setLoansPeripheralAddress(loans_peripheral_contract)
        lendingpool_otc_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)
        collateral_vault_otc_contract.setLoansAddress(loans_peripheral_contract)
        collateral_vault_otc_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)
        liquidations_otc_contract.setLendingPoolContract(lendingpool_otc_contract)
        liquidations_otc_contract.setLoansContract(loans_core_contract)
        liquidations_otc_contract.setCollateralVaultPeripheralAddress(collateral_vault_otc_contract)
        loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)


def test_store_collateral_zero_values(collateral_vault_otc_contract, erc721_contract, borrower):
    with boa.reverts("address is the zero addr"):
        collateral_vault_otc_contract.storeCollateral(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS,
            False,
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS,
            False,
        )

    with boa.reverts("address is the zero addr"):
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            ZERO_ADDRESS,
            False,
        )


def test_store_collateral_wrong_sender(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            False,
        )


def test_store_collateral_not_nft_contract(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    with boa.reverts():
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            False,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral_wrong_owner(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by wallet"):
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            False,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral_not_approved(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(borrower, 0, sender=contract_owner)

    with boa.reverts("transfer is not approved"):
        collateral_vault_otc_contract.storeCollateral(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            False,
            sender=loans_peripheral_contract.address
        )


def test_store_collateral(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_otc_contract, 0, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralStored")

    assert erc721_contract.ownerOf(0) == collateral_vault_otc_contract.address

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._from == borrower


def test_store_cryptopunk_collateral(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, collateral_vault_otc_contract, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralStored")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == collateral_vault_otc_contract.address

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._from == borrower

    cryptopunks_market_contract.transferPunk(borrower, 0, sender=collateral_vault_otc_contract.address)


def test_transfer_collateral_from_loan_zero_values(collateral_vault_otc_contract, erc721_contract, borrower):
    with boa.reverts("address is the zero addr"):
        collateral_vault_otc_contract.transferCollateralFromLoan(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_otc_contract.transferCollateralFromLoan(
            borrower,
            ZERO_ADDRESS,
            0,
            ZERO_ADDRESS
        )

    with boa.reverts("address is the zero addr"):
        collateral_vault_otc_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            ZERO_ADDRESS
        )


def test_transfer_collateral_from_loan_wrong_sender(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract
        )


def test_transfer_collateral_from_loan_not_nft_contract(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    with boa.reverts():
        collateral_vault_otc_contract.transferCollateralFromLoan(
            borrower,
            erc20_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_transfer_collateral_from_loan_wrong_owner(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by vault"):
        collateral_vault_otc_contract.transferCollateralFromLoan(
            borrower,
            erc721_contract,
            0,
            erc20_contract,
            sender=loans_peripheral_contract.address
        )


def test_transfer_collateral_from_loan(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_otc_contract, 0, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_otc_contract.address

    collateral_vault_otc_contract.transferCollateralFromLoan(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralFromLoanTransferred")

    assert erc721_contract.ownerOf(0) == borrower

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_cryptopunk_collateral_from_loan(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, collateral_vault_otc_contract, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )

    assert cryptopunks_market_contract.punkIndexToAddress(0) == collateral_vault_otc_contract.address

    collateral_vault_otc_contract.transferCollateralFromLoan(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        sender=loans_peripheral_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralFromLoanTransferred")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_collateral_from_liquidation_wrong_sender(collateral_vault_otc_contract):
    with boa.reverts("msg.sender is not authorised"):
        collateral_vault_otc_contract.transferCollateralFromLiquidation(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0
        )


def test_transfer_collateral_from_liquidation_zero_values(
    collateral_vault_otc_contract,
    liquidations_otc_contract,
    borrower,
    contract_owner
):

    with boa.reverts("address is the zero addr"):
        collateral_vault_otc_contract.transferCollateralFromLiquidation(
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            0,
            sender=liquidations_otc_contract.address
        )

    with boa.reverts("collat addr is the zero addr"):
        collateral_vault_otc_contract.transferCollateralFromLiquidation(
            borrower,
            ZERO_ADDRESS,
            0,
            sender=liquidations_otc_contract.address
        )


def test_transfer_collateral_from_liquidation_not_nft_contract(
    collateral_vault_otc_contract,
    liquidations_otc_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    with boa.reverts():
        collateral_vault_otc_contract.transferCollateralFromLiquidation(
            borrower,
            erc20_contract,
            0,
            sender=liquidations_otc_contract.address
        )


def test_transfer_collateral_from_liquidation_wrong_owner(
    collateral_vault_otc_contract,
    liquidations_otc_contract,
    erc721_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(contract_owner, 0, sender=contract_owner)

    with boa.reverts("collateral not owned by vault"):
        collateral_vault_otc_contract.transferCollateralFromLiquidation(
            borrower,
            erc721_contract,
            0,
            sender=liquidations_otc_contract.address
        )


def test_transfer_collateral_from_liquidation(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    liquidations_otc_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner
):

    erc721_contract.mint(borrower, 0, sender=contract_owner)
    erc721_contract.approve(collateral_vault_otc_contract, 0, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        erc721_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )

    assert erc721_contract.ownerOf(0) == collateral_vault_otc_contract.address

    collateral_vault_otc_contract.transferCollateralFromLiquidation(
        borrower,
        erc721_contract,
        0,
        sender=liquidations_otc_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralFromLiquidationTransferred")

    assert erc721_contract.ownerOf(0) == borrower

    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event._to == borrower


def test_transfer_punk_from_liquidation(
    collateral_vault_otc_contract,
    loans_peripheral_contract,
    liquidations_otc_contract,
    cryptopunks_market_contract,
    cryptopunk_collaterals,
    erc20_contract,
    borrower,
    contract_owner
):
    cryptopunks_market_contract.offerPunkForSaleToAddress(0, 0, collateral_vault_otc_contract, sender=borrower)

    collateral_vault_otc_contract.storeCollateral(
        borrower,
        cryptopunks_market_contract,
        0,
        erc20_contract,
        False,
        sender=loans_peripheral_contract.address
    )

    assert cryptopunks_market_contract.punkIndexToAddress(0) == collateral_vault_otc_contract.address

    collateral_vault_otc_contract.transferCollateralFromLiquidation(
        borrower,
        cryptopunks_market_contract,
        0,
        sender=liquidations_otc_contract.address
    )
    event = get_last_event(collateral_vault_otc_contract, name="CollateralFromLiquidationTransferred")

    assert cryptopunks_market_contract.punkIndexToAddress(0) == borrower

    assert event.collateralAddress == cryptopunks_market_contract.address
    assert event.tokenId == 0
    assert event._to == borrower
