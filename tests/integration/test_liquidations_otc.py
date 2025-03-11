from dataclasses import dataclass
from datetime import datetime as dt
from decimal import Decimal

import boa
import eth_abi
import pytest
from web3 import Web3

from ..conftest_base import get_events, get_last_event

GRACE_PERIOD_DURATION = 50
PROTOCOL_FEE = 250

MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.to_wei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000


@dataclass
class Liquidation:
    lid: bytes
    collateralAddress: str
    tokenId: int
    startTime: int
    gracePeriodMaturity: int
    principal: int
    interestAmount: int
    apr: int
    gracePeriodPrice: int
    borrower: str
    loanId: int
    loansCoreContract: str
    erc20TokenContract: str


@dataclass
class InvestorFunds:
    currentAmountDeposited: int
    totalAmountDeposited: int
    totalAmountWithdrawn: int
    sharesBasisPoints: int
    activeForRewards: bool


@pytest.fixture(scope="module")
def lendingpool_otc_contract(erc20_contract, lending_pool_eth_otc_contract_def, contract_owner, investor, protocol_wallet):
    with boa.env.prank(contract_owner):
        contract = lending_pool_eth_otc_contract_def.deploy(erc20_contract)
        proxy_address = contract.create_proxy(protocol_wallet, PROTOCOL_FEE, investor)
        return lending_pool_eth_otc_contract_def.at(proxy_address)


@pytest.fixture(scope="module")
def liquidations_otc_contract(
    liquidations_otc_contract_def,
    contract_owner,
    lendingpool_otc_contract,
    loans_core_contract,
    collateral_vault_peripheral_contract,
):
    with boa.env.prank(contract_owner):
        contract = liquidations_otc_contract_def.deploy()
        proxy_address = contract.create_proxy(
            GRACE_PERIOD_DURATION, loans_core_contract, lendingpool_otc_contract, collateral_vault_peripheral_contract
        )
        return liquidations_otc_contract_def.at(proxy_address)


@pytest.fixture(scope="module", autouse=True)
def setup(
    contracts_config,
    lendingpool_otc_contract,
    liquidations_otc_contract,
    erc20_contract,
    loans_peripheral_contract,
    collateral_vault_peripheral_contract,
    contract_owner,
):
    with boa.env.prank(contract_owner):
        lendingpool_otc_contract.setLoansPeripheralAddress(loans_peripheral_contract)
        lendingpool_otc_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)
        collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)
        loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_otc_contract)


def test_add_liquidation(
    liquidations_otc_contract,
    loans_core_contract,
    loans_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner,
):
    erc721_contract.mint(collateral_vault_core_contract, 0, sender=contract_owner)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address,
    )
    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)
    liquidations_otc_contract.addLiquidation(borrower, loan_id, erc20_contract.address)
    event = get_last_event(liquidations_otc_contract, name="LiquidationAdded")

    liquidation = Liquidation(*liquidations_otc_contract.getLiquidation(erc721_contract, 0))
    _, _amount, _interest, _maturity, _start_time, *_ = loans_core_contract.getLoan(borrower, loan_id)

    interest_amount = _amount * _interest // 10000

    apr = LOAN_INTEREST * 365 * 24 * 60 * 60 // (_maturity - _start_time)

    liquidation_id_abi_encoded = eth_abi.encode(
        ["address", "uint256", "uint256"], [erc721_contract.address, 0, liquidation.startTime]
    )
    liquidation_id = Web3.solidity_keccak(["bytes32"], [liquidation_id_abi_encoded]).hex()

    assert liquidation.lid.hex() == liquidation_id
    assert liquidation.gracePeriodMaturity == liquidation.startTime + GRACE_PERIOD_DURATION
    assert liquidation.principal == LOAN_AMOUNT
    assert liquidation.interestAmount == interest_amount
    assert liquidation.apr == apr
    assert liquidation.borrower == borrower
    assert liquidation.loanId == loan_id
    assert liquidation.loansCoreContract == loans_core_contract.address
    assert liquidation.erc20TokenContract == erc20_contract.address

    assert event.liquidationId.hex() == liquidation_id
    assert event.collateralAddress == erc721_contract.address
    assert event.tokenId == 0
    assert event.erc20TokenContract == erc20_contract.address
    assert event.gracePeriodPrice == Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + int(
        min(0.025 * LOAN_AMOUNT, Web3.to_wei(0.2, "ether"))
    )
    assert event.lenderPeriodPrice == Decimal(LOAN_AMOUNT) + Decimal(interest_amount) + int(
        min(0.025 * LOAN_AMOUNT, Web3.to_wei(0.2, "ether"))
    )
    assert event.gracePeriodMaturity == liquidation.startTime + GRACE_PERIOD_DURATION
    assert event.loansCoreContract == loans_core_contract.address
    assert event.loanId == loan_id
    assert event.borrower == borrower

    assert liquidations_otc_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)


def test_add_liquidation_loan_not_defaulted(
    liquidations_otc_contract,
    loans_peripheral_contract,
    loans_core_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner,
):
    erc721_contract.mint(collateral_vault_core_contract, 0, sender=contract_owner)
    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address,
    )

    with boa.reverts("loan is not defaulted"):
        liquidations_otc_contract.addLiquidation(borrower, loan_id, erc20_contract)


def test_pay_loan_liquidations_grace_period(
    liquidations_otc_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lendingpool_otc_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner,
    investor,
):
    erc721_contract.mint(collateral_vault_core_contract, 0, sender=contract_owner)
    erc721_contract.mint(collateral_vault_core_contract, 1, sender=contract_owner)

    lendingpool_otc_contract.depositEth(sender=investor, value=LOAN_AMOUNT * 2)
    lendingpool_otc_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT // 2), (erc721_contract.address, 1, LOAN_AMOUNT // 2)],
        sender=loans_peripheral_contract.address,
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_otc_contract.addLiquidation(borrower, loan_id, erc20_contract)

    liquidation1 = Liquidation(*liquidations_otc_contract.getLiquidation(erc721_contract.address, 0))
    liquidation2 = Liquidation(*liquidations_otc_contract.getLiquidation(erc721_contract.address, 1))

    assert liquidations_otc_contract.lendingPoolContract() == lendingpool_otc_contract.address
    assert lendingpool_otc_contract.erc20TokenContract() == erc20_contract.address
    liquidations_otc_contract.payLoanLiquidationsGracePeriod(
        loan_id, erc20_contract, sender=borrower, value=liquidation1.gracePeriodPrice + liquidation2.gracePeriodPrice
    )

    event_liquidation_removed1, event_liquidation_removed2 = get_events(liquidations_otc_contract, name="LiquidationRemoved")[
        -2:
    ]
    event_nft_purchased1, event_nft_purchased2 = get_events(liquidations_otc_contract, name="NFTPurchased")[-2:]
    fund_receipt_events = get_events(liquidations_otc_contract, name="FundsReceipt")

    # LIQUIDATION 1
    assert event_liquidation_removed1.liquidationId == liquidation1.lid
    assert event_liquidation_removed1.collateralAddress == erc721_contract.address
    assert event_liquidation_removed1.tokenId == 0
    assert event_liquidation_removed1.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed1.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed1.loanId == loan_id
    assert event_liquidation_removed1.borrower == borrower

    assert event_nft_purchased1.liquidationId == liquidation1.lid
    assert event_nft_purchased1.collateralAddress == erc721_contract.address
    assert event_nft_purchased1.tokenId == 0
    assert event_nft_purchased1.amount == liquidation1.gracePeriodPrice
    assert event_nft_purchased1.buyerAddress == borrower
    assert event_nft_purchased1.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased1.method == "GRACE_PERIOD"

    # LIQUIDATION 2
    assert event_liquidation_removed2.liquidationId == liquidation2.lid
    assert event_liquidation_removed2.collateralAddress == erc721_contract.address
    assert event_liquidation_removed2.tokenId == 1
    assert event_liquidation_removed2.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed2.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed2.loanId == loan_id
    assert event_liquidation_removed2.borrower == borrower

    assert event_nft_purchased2.liquidationId == liquidation2.lid
    assert event_nft_purchased2.collateralAddress == erc721_contract.address
    assert event_nft_purchased2.tokenId == 1
    assert event_nft_purchased2.amount == liquidation2.gracePeriodPrice
    assert event_nft_purchased2.buyerAddress == borrower
    assert event_nft_purchased2.erc20TokenContract == erc20_contract.address
    assert event_nft_purchased2.method == "GRACE_PERIOD"

    for event in fund_receipt_events:
        assert event.fundsOrigin == "liquidation_grace_period"

    assert liquidations_otc_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)


def test_claim(
    liquidations_otc_contract,
    loans_peripheral_contract,
    loans_core_contract,
    lendingpool_otc_contract,
    collateral_vault_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    erc20_contract,
    borrower,
    contract_owner,
    investor,
):
    erc721_contract.mint(collateral_vault_core_contract, 0, sender=contract_owner)

    lendingpool_otc_contract.depositEth(sender=investor, value=LOAN_AMOUNT * 2)
    lendingpool_otc_contract.sendFundsEth(contract_owner, LOAN_AMOUNT, sender=loans_peripheral_contract.address)

    assert liquidations_otc_contract.lendingPoolContract() == lendingpool_otc_contract.address
    assert InvestorFunds(*lendingpool_otc_contract.lenderFunds(investor)).currentAmountDeposited == LOAN_AMOUNT * 2

    loan_id = loans_core_contract.addLoan(
        borrower,
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        [(erc721_contract.address, 0, LOAN_AMOUNT)],
        sender=loans_peripheral_contract.address,
    )

    loans_core_contract.updateLoanStarted(borrower, loan_id, sender=loans_peripheral_contract.address)
    loans_core_contract.updateDefaultedLoan(borrower, loan_id, sender=loans_peripheral_contract.address)

    liquidations_otc_contract.addLiquidation(borrower, loan_id, erc20_contract)

    liquidation = Liquidation(*liquidations_otc_contract.getLiquidation(erc721_contract.address, 0))

    boa.env.time_travel(seconds=GRACE_PERIOD_DURATION + 1)
    assert liquidation.erc20TokenContract == erc20_contract.address

    with boa.reverts():
        liquidations_otc_contract.claim(erc721_contract, 0, sender=borrower)

    with boa.reverts():
        liquidations_otc_contract.claim(erc721_contract, 1, sender=investor)

    liquidations_otc_contract.claim(erc721_contract, 0, sender=investor)

    assert erc721_contract.ownerOf(0) == investor

    event_liquidation_removed = get_last_event(liquidations_otc_contract, name="LiquidationRemoved")
    event_nft_claimed = get_last_event(liquidations_otc_contract, name="NFTClaimed")

    # LIQUIDATION
    assert event_liquidation_removed.liquidationId == liquidation.lid
    assert event_liquidation_removed.collateralAddress == erc721_contract.address
    assert event_liquidation_removed.tokenId == 0
    assert event_liquidation_removed.erc20TokenContract == erc20_contract.address
    assert event_liquidation_removed.loansCoreContract == loans_core_contract.address
    assert event_liquidation_removed.loanId == loan_id
    assert event_liquidation_removed.borrower == borrower

    assert event_nft_claimed.liquidationId == liquidation.lid
    assert event_nft_claimed.collateralAddress == erc721_contract.address
    assert event_nft_claimed.tokenId == 0
    assert event_nft_claimed.amount == liquidation.gracePeriodPrice
    assert event_nft_claimed.buyerAddress == investor
    assert event_nft_claimed.erc20TokenContract == erc20_contract.address
    assert event_nft_claimed.method == "OTC_CLAIM"

    assert liquidations_otc_contract.isLoanLiquidated(borrower, loans_core_contract, loan_id)
