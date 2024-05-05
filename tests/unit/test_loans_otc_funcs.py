from dataclasses import dataclass
from decimal import Decimal
from textwrap import dedent

import boa
import pytest
from eth_abi import encode
from eth_account import Account
from eth_account.messages import HexBytes, SignableMessage
from eth_utils import keccak
from hypothesis import given, settings
from hypothesis import strategies as st
from web3 import Web3

from ..conftest_base import ZERO_ADDRESS, get_last_event

NOW = boa.eval("block.timestamp")
MATURITY = NOW + 7 * 86400
LOAN_AMOUNT = 10**17
LOAN_INTEREST = 250
INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60
VALIDATION_DEADLINE = MATURITY + 1800


@dataclass
class LoanInfo:
    id: int
    amount: int
    interest: int
    maturity: int
    startTime: int
    collaterals: list
    paidPrincipal: int
    paidInterestAmount: int
    started: bool
    invalidated: bool
    paid: bool
    defaulted: bool
    canceled: bool


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


@pytest.fixture(scope="module", autouse=True)
def contract_owner(owner_account):
    return owner_account.address


@pytest.fixture(scope="module")
def borrower():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def erc20(weth9_contract, contract_owner):
    with boa.env.prank(contract_owner):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def erc721(erc721_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return erc721_contract.deploy()


@pytest.fixture(scope="module")
def lending_pool():
    return boa.loads(
        dedent("""
    @view
    @external
    def maxFundsInvestable() -> uint256:
        return 10**60

    @view
    @external
    def erc20TokenContract() -> address:
        return empty(address)

    # @external
    # def sendFundsEth(_to: address, _amount: uint256):
    #     pass

    # @external
    # def sendFunds(_to: address, _amount: uint256):
    #     pass

    # @external
    # def receiveFundsEth(_borrower: address, _amount: uint256, _rewardsAmount: uint256):
    #     pass

    @external
    @payable
    def __default__():
        pass
     """)
    )


@pytest.fixture(scope="module")
def collateral_vault(empty_contract):
    return boa.loads(
        dedent("""
    @external
    def storeCollateral(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _createDelegation: bool):
        pass

    @external
    def transferCollateralFromLoan(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address):
        pass

    @external
    def isCollateralApprovedForVault(_borrower: address, _collateralAddress: address, _tokenId: uint256) -> bool:
        return _tokenId < 100

    @external
    def setCollateralDelegation(_wallet: address, _collateralAddress: address, _tokenId: uint256, _erc20TokenContract: address, _value: bool):
        pass
     """)
    )


@pytest.fixture(scope="module")
def liquidations(empty_contract):
    return boa.loads(
        dedent("""
    @external
    def addLiquidation(_borrower: address, _loanId: uint256, _erc20TokenContract: address):
        pass
     """)
    )


@pytest.fixture(scope="module")
def genesis(erc721_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return erc721_contract.deploy()


@pytest.fixture(scope="module")
def loans_otc_impl(loans_otc_contract, contract_owner):
    with boa.env.prank(contract_owner):
        return loans_otc_contract.deploy()


@pytest.fixture(scope="module")
def loans(loans_otc_contract, loans_otc_impl, contract_owner, lending_pool, collateral_vault, genesis, liquidations):
    with boa.env.prank(contract_owner):
        proxy_address = loans_otc_impl.create_proxy(INTEREST_ACCRUAL_PERIOD, lending_pool, collateral_vault, genesis, True)
        proxy = loans_otc_contract.at(proxy_address)
        proxy.setLiquidationsPeripheralAddress(liquidations)
        return proxy


@pytest.fixture(scope="module")
def test_collaterals(erc721):
    return [(erc721.address, k, LOAN_AMOUNT // 5) for k in range(5)]


@pytest.fixture(name="create_signature", scope="module")
def create_signature_fixture(test_collaterals, loans, owner_account, borrower):
    # Can't use eth_account.messages.encode_structured_data (as of version 0.5.9) because dynamic arrays are not correctly hashed:
    # https://github.com/ethereum/eth-account/blob/v0.5.9/eth_account/_utils/structured_data/hashing.py#L236
    # Probably fixed (https://github.com/ethereum/eth-account/commit/e6c3136bd30d2ec4738c2ca32329d2d119539f1a) so it can be used when brownie allows eth-account==0.7.0

    def _create_signature(
        collaterals=test_collaterals,
        delegations=False,
        amount=LOAN_AMOUNT,
        interest=LOAN_INTEREST,
        maturity=MATURITY,
        deadline=VALIDATION_DEADLINE,
        nonce=0,
        genesis_token=0,
        borrower=borrower,
        signer=owner_account,
        verifier=loans,
        domain_name="Zharta",
        domain_version="1",
        chain_id=boa.env.evm.chain.chain_id,
    ):
        print(
            f"_create_signature {collaterals=} {delegations=} {amount=} {interest=} {maturity=} {deadline=} {nonce=} {genesis_token=} {borrower=} {signer=} {verifier=} {chain_id=}"
        )
        domain_type_def = "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        reserve_type_def = "ReserveMessageContent(address borrower,uint256 amount,uint256 interest,uint256 maturity,Collateral[] collaterals,bool delegations,uint256 deadline,uint256 nonce,uint256 genesisToken)"
        collateral_type_def = "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"

        domain_type_hash = keccak(text=domain_type_def)
        reserve_type_hash = keccak(text=reserve_type_def + collateral_type_def)
        collateral_type_hash = keccak(text=collateral_type_def)

        domain_instance = encode(
            ["bytes32", "bytes32", "bytes32", "uint256", "address"],
            [
                domain_type_hash,
                keccak(text=domain_name),
                keccak(text=domain_version),
                chain_id,
                verifier.address,
            ],
        )
        domain_hash = keccak(domain_instance)

        struct_instance = encode(
            [
                "bytes32",
                "address",
                "uint256",
                "uint256",
                "uint256",
                "bytes32",
                "bool",
                "uint256",
                "uint256",
                "uint256",
            ],
            [
                reserve_type_hash,
                borrower,
                amount,
                interest,
                maturity,
                keccak(
                    encode(
                        ["bytes32"] * len(collaterals),
                        [
                            keccak(
                                encode(
                                    ["bytes32", "address", "uint256", "uint256"],
                                    [collateral_type_hash, c[0], c[1], int(c[2])],
                                )
                            )
                            for c in collaterals
                        ],
                    )
                ),
                delegations,
                deadline,
                nonce,
                genesis_token,
            ],
        )

        message_hash = keccak(struct_instance)
        signed_message = Account.sign_message(
            SignableMessage(HexBytes(b"\x01"), domain_hash, message_hash),
            private_key=signer.key,
        )
        return (signed_message.v, signed_message.r, signed_message.s)

    return _create_signature


def test_create_deprecated(
    loans,
    create_signature,
    contract_owner,
    borrower,
    test_collaterals,
):
    loans.deprecate(sender=contract_owner)
    (v, r, s) = create_signature()
    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_create_not_accepting_loans(
    loans,
    create_signature,
    contract_owner,
    borrower,
    test_collaterals,
):
    loans.changeContractStatus(False, sender=contract_owner)
    (v, r, s) = create_signature()

    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_create_maturity_in_the_past(
    loans,
    collateral_vault,
    lending_pool,
    create_signature,
    erc721,
    borrower,
    investor,
    contract_owner,
    test_collaterals,
):
    maturity = boa.eval("block.timestamp") - 3600
    (v, r, s) = create_signature(maturity=maturity)

    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)

    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            maturity,
            test_collaterals,
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_create_loan_collateral_not_approved(
    loans,
    collateral_vault,
    create_signature,
    lending_pool,
    erc721,
    contract_owner,
    investor,
    borrower,
):
    test_collaterals = [(erc721.address, 100 + k, LOAN_AMOUNT // 5) for k in range(5)]

    for k in range(5):
        erc721.mint(borrower, 100 + k, sender=contract_owner)

    (v, r, s) = create_signature()

    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )
        print(f"{loans.getLoan(borrower, 0)=}")


def test_create_loan_sum_collaterals_amounts_not_amount(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    investor,
    borrower,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)

    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature(collaterals=[(erc721.address, k, 0) for k in range(5)])

    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721.address, k, 0) for k in range(5)],
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_create_loan(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature()

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )
    event = get_last_event(loans, name="LoanCreated")

    loan_details = loans.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)

    assert loan_details.id == loan_id
    assert loan_details.amount == LOAN_AMOUNT
    assert loan_details.interest == LOAN_INTEREST
    assert loan_details.paidPrincipal == 0
    assert loan_details.paidInterestAmount == 0
    assert loan_details.maturity == MATURITY
    assert len(loan_details.collaterals) == 5
    assert loan_details.collaterals == test_collaterals
    assert loan_details.started == True
    assert loan_details.invalidated == False
    assert loan_details.paid == False
    assert loan_details.defaulted == False
    assert loan_details.canceled == False

    assert event.wallet == borrower
    assert event.loanId == 0


def test_create_loan_wrong_signature(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    not_owner_account,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    signature_inconsistencies = [
        ("amount", LOAN_AMOUNT + 1),
        ("interest", LOAN_INTEREST + 1),
        ("maturity", MATURITY + 1),
        ("deadline", VALIDATION_DEADLINE + 1),
        (
            "collaterals",
            [(lending_pool.address, c[1], c[2]) for c in test_collaterals],
        ),
        ("collaterals", [(c[0], c[1] + 1, c[2]) for c in test_collaterals]),
        ("collaterals", [(c[0], c[1], c[2] // 10) for c in test_collaterals]),
        ("collaterals", test_collaterals[1:]),
        ("signer", not_owner_account),
        ("verifier", lending_pool),
        ("domain_name", "Other"),
        ("domain_version", "2"),
        ("chain_id", 42),
    ]
    for k, v in signature_inconsistencies:
        print(f"creating signature with {k} = {v}")
        (v, r, s) = create_signature(**{k: v})
        with boa.reverts():
            loans.reserveEth(
                LOAN_AMOUNT,
                LOAN_INTEREST,
                MATURITY,
                test_collaterals,
                False,
                VALIDATION_DEADLINE,
                0,
                0,
                v,
                r,
                s,
                sender=borrower,
            )


def test_create_loan_past_signature_deadline(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    deadline_in_the_past = boa.eval("block.timestamp") - 10
    (v, r, s) = create_signature(deadline=deadline_in_the_past)

    with boa.reverts():
        loans.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            test_collaterals,
            False,
            deadline_in_the_past,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_pay_loan_not_issued(loans, borrower):
    with boa.reverts():
        loans.pay(0, sender=borrower)


def test_pay_loan_defaulted(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    erc20,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    maturity = boa.eval("block.timestamp") + 10
    (v, r, s) = create_signature(maturity=maturity)

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        maturity,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    loan = loans.getLoan(borrower, loan_id)
    loan = LoanInfo(*loan)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    # erc20.mint(borrower, amount_paid, sender=contract_owner)
    erc20.approve(lending_pool, amount_paid, sender=borrower)

    boa.env.time_travel(seconds=15)
    with boa.reverts():
        loans.pay(loan.id, sender=borrower)


def test_pay_loan_insufficient_balance(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    erc20,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature()

    loan_id = loans.reserve(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    erc20.eval(f"self.balanceOf[{borrower}] = {LOAN_AMOUNT}")
    assert erc20.balanceOf(borrower) == LOAN_AMOUNT

    erc20.approve(lending_pool, LOAN_AMOUNT * 10, sender=borrower)

    with boa.reverts():
        loans.pay(loan_id, sender=borrower)


def test_pay_loan_insufficient_allowance(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    erc20,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    # erc20.mint(borrower, amount_paid - LOAN_AMOUNT, sender=contract_owner)

    (v, r, s) = create_signature()

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    erc20.approve(lending_pool, amount_paid // 2, sender=borrower)
    boa.env.set_balance(borrower, amount_paid)

    with boa.reverts():
        loans.pay(loan_id, sender=borrower)

    with boa.reverts():
        loans.pay(loan_id, sender=borrower, value=amount_paid // 2)


def test_pay_loan(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature()

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    boa.env.time_travel(seconds=6 * 86400)

    loan_details = loans.getLoan(borrower, loan_id)
    payable_amount = loans.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))

    boa.env.set_balance(borrower, payable_amount)
    loans.pay(loan_id, sender=borrower, value=payable_amount)
    loan_paid_event = get_last_event(loans, name="LoanPaid")
    loan_payment_event = get_last_event(loans, name="LoanPayment")

    loan_details = loans.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)
    assert loans.getLoanPaid(borrower, loan_id)
    assert loans.getLoanPaidPrincipal(borrower, loan_id) + loans.getLoanPaidInterestAmount(borrower, loan_id) == payable_amount
    assert loan_details.paid == loans.getLoanPaid(borrower, loan_id)
    assert loan_details.paidPrincipal == loans.getLoanPaidPrincipal(borrower, loan_id)
    assert loan_details.paidInterestAmount == loans.getLoanPaidInterestAmount(borrower, loan_id)
    assert loans.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp")) == 0

    assert loan_paid_event.wallet == borrower
    assert loan_paid_event.loanId == loan_id
    assert loan_payment_event.wallet == borrower
    assert loan_payment_event.loanId == loan_id
    assert loan_payment_event.principal + loan_payment_event.interestAmount == payable_amount

    for collateral in test_collaterals:
        assert erc721.ownerOf(collateral[1]) == borrower


def test_pay_loan_already_paid(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature()

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        MATURITY,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    loan_details = loans.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)

    payable_amount = loans.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))

    boa.env.set_balance(borrower, payable_amount * 2)
    loans.pay(loan_id, sender=borrower, value=payable_amount)

    with boa.reverts():
        loans.pay(loan_id, sender=borrower, value=payable_amount)


def test_set_default_loan_wrong_sender(loans, investor, borrower):
    with boa.reverts():
        loans.settleDefault(borrower, 0, sender=investor)


def test_set_default_loan_not_started(loans, contract_owner, borrower):
    with boa.reverts():
        loans.settleDefault(borrower, 0, sender=contract_owner)


def test_set_default_loan(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    liquidations_otc_contract,
    erc721,
    erc20,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    maturity = boa.eval("block.timestamp") + 10
    (v, r, s) = create_signature(maturity=maturity)

    loan_id = loans.reserveEth(
        LOAN_AMOUNT,
        LOAN_INTEREST,
        maturity,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    loan = loans.getLoan(borrower, loan_id)
    loan = LoanInfo(*loan)

    boa.env.time_travel(seconds=15)

    print(loans.getLoanMaturity(borrower, loan_id))
    print(loans.getLoanDefaulted(borrower, loan_id))
    print(boa.eval("block.timestamp"))

    loans.settleDefault(borrower, loan_id, sender=contract_owner)

    assert loans.getLoanDefaulted(borrower, loan_id)


@given(
    loan_duration=st.integers(min_value=1, max_value=90),
    passed_time=st.integers(min_value=1, max_value=200),
    interest=st.integers(min_value=0, max_value=10000),
)
@settings(max_examples=5, deadline=1500)
def test_payable_amount(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
    loan_duration,
    passed_time,
    interest,
):
    amount = LOAN_AMOUNT
    maturity = NOW + loan_duration * 24 * 3600

    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    (v, r, s) = create_signature(maturity=maturity, interest=interest)

    loan_id = loans.reserveEth(
        amount,
        interest,
        maturity,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        0,
        v,
        r,
        s,
        sender=borrower,
    )

    boa.env.time_travel(seconds=passed_time * 86400)

    loan_details = loans.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)
    payable_amount = loans.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))

    contract_time_passed = boa.eval("block.timestamp") - loan_details.startTime
    loan_duration_in_contract = maturity - loan_details.startTime
    minimum_interest_period = 7 * 86400

    payable_duration = max(
        minimum_interest_period,
        contract_time_passed + INTEREST_ACCRUAL_PERIOD - contract_time_passed % INTEREST_ACCRUAL_PERIOD,
    )
    due_amount = (
        amount * (loan_duration_in_contract * 10000 + interest * payable_duration) // (loan_duration_in_contract * 10000)
    )

    assert payable_amount == due_amount


def test_genesis_pass_validation(
    loans,
    create_signature,
    lending_pool,
    collateral_vault,
    erc721,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
    genesis,
):
    genesis_token = 1
    amount = LOAN_AMOUNT
    maturity = NOW + 7 * 24 * 3600
    interest = 15

    for k in range(5):
        erc721.mint(borrower, k, sender=contract_owner)
    erc721.setApprovalForAll(collateral_vault, True, sender=borrower)

    print(f"{genesis_token=} {borrower=}")

    genesis.mint(borrower, genesis_token, sender=contract_owner)

    (v, r, s) = create_signature(maturity=maturity, interest=interest, genesis_token=genesis_token)

    loans.reserveEth(
        amount,
        interest,
        maturity,
        test_collaterals,
        False,
        VALIDATION_DEADLINE,
        0,
        genesis_token,
        v,
        r,
        s,
        sender=borrower,
    )

    event = get_last_event(loans, name="LoanCreated")
    assert event.genesisToken == genesis_token
