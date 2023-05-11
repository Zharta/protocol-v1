import datetime as dt
import boa
import time

from hypothesis import settings, given
from hypothesis import strategies as st
from decimal import Decimal
from web3 import Web3

import pytest
from eth_account.messages import SignableMessage, HexBytes
from eth_account import Account
from eth_utils import keccak
from eth_abi import encode

from ..conftest_base import ZERO_ADDRESS, get_last_event
from dataclasses import dataclass


MAX_LOAN_DURATION = 31 * 24 * 60 * 60  # 31 days
MATURITY = int(dt.datetime.now().timestamp()) + 30 * 24 * 60 * 60
VALIDATION_DEADLINE = int(dt.datetime.now().timestamp()) + 30 * 60 * 60
LOAN_AMOUNT = Web3.to_wei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000
INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60

PROTOCOL_FEES_SHARE = 2500  # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000  # parts per 10000, e.g. 2.5% is 250 parts per 10000

GRACE_PERIOD_DURATION = 5
LENDER_PERIOD_DURATION = 5
AUCTION_DURATION = 5

MAX_LOANS_POOL_SHARE = 1500  # parts per 10000, e.g. 2.5% is 250 parts per 10000


@dataclass
class LoanInfo():
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
class Liquidation():
    lid: bytes
    collateralAddress: str
    tokenId: int
    startTime: int
    gracePeriodMaturity: int
    lenderPeriodMaturity: int
    principal: int
    interestAmount: int
    apr: int
    gracePeriodPrice: int
    lenderPeriodPrice: int
    borrower: str
    loanId: int
    loansCoreContract: str
    erc20TokenContract: str
    inAuction: bool



@pytest.fixture(name="create_signature", scope="module", autouse=True)
def create_signature_fixture(
    test_collaterals, loans_peripheral_contract, owner_account, borrower
):

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
        verifier=loans_peripheral_contract,
        domain_name="Zharta",
        domain_version="1",
        chain_id=boa.env.chain.chain_id,
    ):

        domain_type_def = "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        reserve_type_def = "ReserveMessageContent(address borrower,uint256 amount,uint256 interest,uint256 maturity,Collateral[] collaterals,bool delegations,uint256 deadline,uint256 nonce,uint256 genesisToken)"
        collateral_type_def = (
            "Collateral(address contractAddress,uint256 tokenId,uint256 amount)"
        )

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


# def test_settle_default_lender_zeroaddress(
#     loans_peripheral_contract,
#     create_signature,
#     loans_core_contract,
#     lending_pool_peripheral_contract,
#     lending_pool_core_contract,
#     lending_pool_lock_contract,
#     collateral_vault_peripheral_contract,
#     collateral_vault_core_contract,
#     liquidity_controls_contract,
#     erc721_contract,
#     erc20_contract,
#     contract_owner,
#     investor,
#     borrower,
#     test_collaterals,
# ):
#     lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
#     lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
#     lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, sender=contract_owner)
#     lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, sender=contract_owner)
#     loans_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, sender=contract_owner)
#     collateral_vault_core_contract.setCollateralVaultPeripheralAddress(
#         collateral_vault_peripheral_contract, sender=contract_owner
#     )
#     collateral_vault_peripheral_contract.addLoansPeripheralAddress(
#         erc20_contract, loans_peripheral_contract, sender=contract_owner
#     )
#     loans_core_contract.setLoansPeripheral(loans_peripheral_contract, sender=contract_owner)

#     lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

#     for k in range(5):
#         erc721_contract.mint(borrower, k, sender=contract_owner)
#     erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, sender=borrower)

#     maturity = boa.eval("block.timestamp") + 10
#     (v, r, s) = create_signature(maturity=maturity)

#     loan_id = loans_peripheral_contract.reserveEth(
#         LOAN_AMOUNT,
#         LOAN_INTEREST,
#         maturity,
#         test_collaterals,
#         False,
#         VALIDATION_DEADLINE,
#         0,
#         0,
#         v,
#         r,
#         s,
#         sender=borrower,
#     )

#     boa.env.time_travel(seconds=15)

#     with boa.reverts("BNPeriph is the zero address"):
#         loans_peripheral_contract.settleDefault(borrower, loan_id, sender=contract_owner)


def test_load_contract_config(contracts_config):
    pass  # contracts_config fixture active from this point on


def test_initial_state(loans_peripheral_contract, contract_owner):
    # Check if the constructor of the contract is set up properly
    assert loans_peripheral_contract.owner() == contract_owner
    assert loans_peripheral_contract.isAcceptingLoans() == True
    assert loans_peripheral_contract.isDeprecated() == False


def test_propose_owner_wrong_sender(loans_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.proposeOwner(borrower, sender=borrower)


def test_propose_owner_zero_address(loans_peripheral_contract, contract_owner):
    with boa.reverts("_address it the zero address"):
        loans_peripheral_contract.proposeOwner(
            ZERO_ADDRESS, sender=contract_owner
        )


def test_propose_owner_same_owner(loans_peripheral_contract, contract_owner):
    with boa.reverts("proposed owner addr is the owner"):
        loans_peripheral_contract.proposeOwner(contract_owner, sender=contract_owner)


def test_propose_owner(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, sender=contract_owner)
    event = get_last_event(loans_peripheral_contract, name="OwnerProposed")

    assert loans_peripheral_contract.proposedOwner() == borrower
    assert loans_peripheral_contract.owner() == contract_owner
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_propose_owner_same_proposed(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("proposed owner addr is the same"):
        loans_peripheral_contract.proposeOwner(borrower, sender=contract_owner)


def test_claim_ownership_wrong_sender(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    with boa.reverts("msg.sender is not the proposed"):
        loans_peripheral_contract.claimOwnership(sender=contract_owner)


def test_claim_ownership(loans_peripheral_contract, contract_owner, borrower):
    loans_peripheral_contract.proposeOwner(borrower, sender=contract_owner)

    loans_peripheral_contract.claimOwnership(sender=borrower)
    event = get_last_event(loans_peripheral_contract, name="OwnershipTransferred")

    assert loans_peripheral_contract.owner() == borrower
    assert loans_peripheral_contract.proposedOwner() == ZERO_ADDRESS
    assert event.owner == contract_owner
    assert event.proposedOwner == borrower


def test_set_lending_pool_address_not_owner(loans_peripheral_contract, lending_pool_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=borrower)


def test_set_lending_pool_address_zero_address(loans_peripheral_contract, contract_owner):
    with boa.reverts("_address is the zero address"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(ZERO_ADDRESS, sender=contract_owner)


def test_set_lending_pool_address_not_contract(loans_peripheral_contract, contract_owner):
    with boa.reverts("_address is not a contract"):
        loans_peripheral_contract.setLendingPoolPeripheralAddress(contract_owner, sender=contract_owner)


def test_set_lending_pool_address(
    loans_peripheral_contract,
    lending_pool_peripheral_contract,
    lending_pool_peripheral_contract_aux,
    contract_owner,
):
    loans_peripheral_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract_aux, sender=contract_owner)
    event = get_last_event(loans_peripheral_contract, name="LendingPoolPeripheralAddressSet")

    assert (loans_peripheral_contract.lendingPoolPeripheralContract() == lending_pool_peripheral_contract_aux.address)
    assert event.currentValue == lending_pool_peripheral_contract.address
    assert event.newValue == lending_pool_peripheral_contract_aux.address

    loans_peripheral_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, sender=contract_owner)
    event = get_last_event(loans_peripheral_contract, name="LendingPoolPeripheralAddressSet")

    assert loans_peripheral_contract.lendingPoolPeripheralContract() == lending_pool_peripheral_contract.address
    assert event.currentValue == lending_pool_peripheral_contract_aux.address
    assert event.newValue == lending_pool_peripheral_contract.address


def test_change_contract_status_wrong_sender(loans_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.changeContractStatus(False, sender=borrower)


def test_change_contract_status_same_status(loans_peripheral_contract, contract_owner):
    with boa.reverts("new contract status is the same"):
        loans_peripheral_contract.changeContractStatus(True, sender=contract_owner)


def test_change_contract_status(loans_peripheral_contract, contract_owner):
    loans_peripheral_contract.changeContractStatus(False, sender=contract_owner)
    event = get_last_event(loans_peripheral_contract, name="ContractStatusChanged")

    assert not loans_peripheral_contract.isAcceptingLoans()
    assert not event.value


def test_deprecate_wrong_sender(loans_peripheral_contract, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.deprecate(sender=borrower)


def test_deprecate(loans_peripheral_contract, contract_owner):
    loans_peripheral_contract.deprecate(sender=contract_owner)
    event = get_last_event(loans_peripheral_contract, name="ContractDeprecated")

    assert loans_peripheral_contract.isDeprecated() == True
    assert loans_peripheral_contract.isAcceptingLoans() == False
    assert event is not None


def test_deprecate_already_deprecated(loans_peripheral_contract, contract_owner):
    loans_peripheral_contract.deprecate(sender=contract_owner)

    with boa.reverts("contract is already deprecated"):
        loans_peripheral_contract.deprecate(sender=contract_owner)


def test_create_deprecated(
    loans_peripheral_contract,
    create_signature,
    contract_owner,
    borrower,
    test_collaterals,
):
    loans_peripheral_contract.deprecate(sender=contract_owner)
    (v, r, s) = create_signature()
    with boa.reverts("contract is deprecated"):
        loans_peripheral_contract.reserveEth(
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
    loans_peripheral_contract,
    create_signature,
    contract_owner,
    borrower,
    test_collaterals,
):
    loans_peripheral_contract.changeContractStatus(False, sender=contract_owner)
    (v, r, s) = create_signature()

    with boa.reverts("contract is not accepting loans"):
        loans_peripheral_contract.reserveEth(
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
    loans_peripheral_contract,
    create_signature,
    borrower,
    test_collaterals,
):
    maturity = int(dt.datetime.now().timestamp()) - 3600
    (v, r, s) = create_signature(maturity=maturity)

    with boa.reverts("maturity is in the past"):
        loans_peripheral_contract.reserveEth(
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


def test_create_collaterals_not_owned(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    erc721_contract.mint(investor, 0, sender=contract_owner)
    (v, r, s) = create_signature()

    with boa.reverts("msg.sender does not own all NFTs"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan_collateral_not_approved(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)

    (v, r, s) = create_signature()

    with boa.reverts("not all NFTs are approved"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan_sum_collaterals_amounts_not_amount(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)

    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature(
        collaterals=[(erc721_contract.address, k, 0) for k in range(5)]
    )

    with boa.reverts("amount in collats != than amount"):
        loans_peripheral_contract.reserveEth(
            LOAN_AMOUNT,
            LOAN_INTEREST,
            MATURITY,
            [(erc721_contract.address, k, 0) for k in range(5)],
            False,
            VALIDATION_DEADLINE,
            0,
            0,
            v,
            r,
            s,
            sender=borrower,
        )


def test_create_loan_unsufficient_funds_in_lp(
    loans_peripheral_contract,
    create_signature,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    test_collaterals,
):
    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)

    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    with boa.reverts("insufficient liquidity"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan_outside_pool_share(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    liquidity_controls_contract.changeMaxLoansPoolShareConditions(
        True, MAX_LOANS_POOL_SHARE, sender=contract_owner
    )
    lending_pool_peripheral_contract.depositEth(sender=investor, value=LOAN_AMOUNT * 2)

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    with boa.reverts("max loans pool share surpassed"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan_outside_collection_share(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    liquidity_controls_contract.changeMaxCollectionBorrowableAmount(
        True, erc721_contract, LOAN_AMOUNT // 10, sender=contract_owner
    )
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    with boa.reverts("max collection share surpassed"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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
    event = get_last_event(loans_peripheral_contract, name="LoanCreated")

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
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

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract.address

    assert event.wallet == borrower
    assert event.loanId == 0


def test_create_loan_wrong_signature(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    not_owner_account,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    liquidity_controls_contract.changeMaxLoansPoolShareConditions(
        True, MAX_LOANS_POOL_SHARE, sender=contract_owner
    )
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    signature_inconsistencies = [
        ("amount", LOAN_AMOUNT + 1),
        ("interest", LOAN_INTEREST + 1),
        ("maturity", MATURITY + 1),
        ("deadline", VALIDATION_DEADLINE + 1),
        (
            "collaterals",
            [
                (lending_pool_peripheral_contract.address, c[1], c[2])
                for c in test_collaterals
            ],
        ),
        ("collaterals", [(c[0], c[1] + 1, c[2]) for c in test_collaterals]),
        ("collaterals", [(c[0], c[1], c[2] // 10) for c in test_collaterals]),
        ("collaterals", test_collaterals[1:]),
        ("signer", not_owner_account),
        ("verifier", loans_core_contract),
        ("domain_name", "Other"),
        ("domain_version", "2"),
        ("chain_id", 42),
    ]
    for (k, v) in signature_inconsistencies:
        print(f"creating signature with {k} = {v}")
        (v, r, s) = create_signature(**{k: v})
        with boa.reverts("invalid message signature"):
            loans_peripheral_contract.reserveEth(
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
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    deadline_in_the_past = boa.eval("block.timestamp") - 10
    (v, r, s) = create_signature(deadline=deadline_in_the_past)

    with boa.reverts("deadline has passed"):
        loans_peripheral_contract.reserveEth(
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


def test_create_loan_within_pool_share(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    liquidity_controls_contract.changeMaxLoansPoolShareConditions(
        True, MAX_LOANS_POOL_SHARE, sender=contract_owner
    )
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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
    event = get_last_event(loans_peripheral_contract, name="LoanCreated")

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
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

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract.address

    assert event.wallet == borrower
    assert event.loanId == 0


def test_create_loan_within_collection_share(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidity_controls_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    liquidity_controls_contract.changeMaxCollectionBorrowableAmount(
        True, erc721_contract, LOAN_AMOUNT, sender=contract_owner
    )
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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
    event = get_last_event(loans_peripheral_contract, name="LoanCreated")

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
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

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract.address

    assert event.wallet == borrower
    assert event.loanId == 0


def test_pay_loan_not_issued(loans_peripheral_contract, borrower):
    with boa.reverts("loan not found"):
        loans_peripheral_contract.pay(0, sender=borrower)


def test_pay_loan_defaulted(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    maturity = boa.eval("block.timestamp") + 10
    (v, r, s) = create_signature(maturity=maturity)

    loan_id = loans_peripheral_contract.reserveEth(
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

    loan = loans_core_contract.getLoan(borrower, loan_id)
    loan = LoanInfo(*loan)

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))
    # erc20_contract.mint(borrower, amount_paid, sender=contract_owner)
    erc20_contract.approve(lending_pool_core_contract, amount_paid, sender=borrower)

    boa.env.time_travel(seconds=15)
    with boa.reverts("loan maturity reached"):
        loans_peripheral_contract.pay(loan.id, sender=borrower)


def test_pay_loan_insufficient_balance(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserve(
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

    initial_borrower_amount = erc20_contract.balanceOf(borrower)
    transfer_amount = initial_borrower_amount - LOAN_AMOUNT
    erc20_contract.transfer(contract_owner, transfer_amount, sender=borrower)

    assert erc20_contract.balanceOf(borrower) == LOAN_AMOUNT

    erc20_contract.approve(lending_pool_core_contract, amount_paid, sender=borrower)

    with boa.reverts("insufficient balance"):
        loans_peripheral_contract.pay(loan_id, sender=borrower)

    erc20_contract.transfer(borrower, transfer_amount, sender=contract_owner)


def test_pay_loan_insufficient_allowance(
    loans_peripheral_contract,
    create_signature,
    lending_pool_peripheral_contract,
    lending_pool_core_contract,
    collateral_vault_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    amount_paid = int(LOAN_AMOUNT * Decimal(f"{(10000 + LOAN_INTEREST) / 10000}"))

    # erc20_contract.mint(borrower, amount_paid - LOAN_AMOUNT, sender=contract_owner)

    borrower_initial_balance = boa.env.get_balance(borrower)

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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

    assert boa.env.get_balance(borrower) == borrower_initial_balance + LOAN_AMOUNT

    erc20_contract.approve(lending_pool_core_contract, amount_paid // 2, sender=borrower)

    with boa.reverts("insufficient allowance"):
        loans_peripheral_contract.pay(loan_id, sender=borrower)

    with boa.reverts("insufficient value received"):
        loans_peripheral_contract.pay(loan_id, sender=borrower, value= amount_paid // 2)


def test_pay_loan(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    borrower_initial_balance = boa.env.get_balance(borrower)

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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

    boa.env.time_travel(seconds=14 * 86400)

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
    payable_amount = loans_peripheral_contract.getLoanPayableAmount(
        borrower, loan_id, boa.eval("block.timestamp")
    )

    assert boa.env.get_balance(borrower) == borrower_initial_balance + LOAN_AMOUNT

    loans_peripheral_contract.pay(loan_id, sender=borrower, value=payable_amount)
    loan_paid_event = get_last_event(loans_peripheral_contract, name="LoanPaid")
    loan_payment_event = get_last_event(loans_peripheral_contract, name="LoanPayment")

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)
    assert loans_core_contract.getLoanPaid(borrower, loan_id)
    assert (
        loans_core_contract.getLoanPaidPrincipal(borrower, loan_id)
        + loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id)
        == payable_amount
    )
    assert loan_details.paid == loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loan_details.paidPrincipal == loans_core_contract.getLoanPaidPrincipal(
        borrower, loan_id
    )
    assert loan_details.paidInterestAmount == loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id)
    assert loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))== 0

    assert loan_paid_event.wallet == borrower
    assert loan_paid_event.loanId == loan_id
    assert loan_payment_event.wallet == borrower
    assert loan_payment_event.loanId == loan_id
    assert loan_payment_event.principal + loan_payment_event.interestAmount == payable_amount

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert boa.env.get_balance(borrower) + payable_amount == borrower_initial_balance + LOAN_AMOUNT


def test_pay_loan_usdc(
    usdc_contracts_config,
    usdc_loans_peripheral_contract,
    create_signature,
    usdc_loans_core_contract,
    usdc_lending_pool_peripheral_contract,
    usdc_lending_pool_core_contract,
    collateral_vault_core_contract,
    erc721_contract,
    usdc_contract,
    contract_owner,
    borrower,
    investor,
):
    amount = 10**9  # 1000 USDC

    usdc_contract.approve(usdc_lending_pool_core_contract, 2*amount, sender=investor)
    usdc_lending_pool_peripheral_contract.deposit(2*amount, sender=investor)

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, sender=borrower)
    test_collaterals = [(erc721_contract.address, k, amount // 5) for k in range(5)]

    borrower_initial_balance = usdc_contract.balanceOf(borrower)

    usdc_contract.approve(usdc_loans_core_contract, amount, sender=borrower)

    (v, r, s) = create_signature(amount=amount, collaterals=test_collaterals, verifier=usdc_loans_peripheral_contract)

    loan_id = usdc_loans_peripheral_contract.reserve(amount, LOAN_INTEREST, MATURITY, test_collaterals, False, VALIDATION_DEADLINE, 0, 0, v, r, s, sender=borrower)

    boa.env.time_travel(seconds=14 * 86400)

    usdc_loans_core_contract.getLoan(borrower, loan_id)
    payable_amount = usdc_loans_peripheral_contract.getLoanPayableAmount(
        borrower, loan_id, boa.eval("block.timestamp")
    )

    assert usdc_contract.balanceOf(borrower) == borrower_initial_balance + amount

    usdc_contract.approve(usdc_lending_pool_core_contract, payable_amount, sender=borrower)
    usdc_loans_peripheral_contract.pay(loan_id, sender=borrower)

    loan_paid_event = get_last_event(usdc_loans_peripheral_contract, name="LoanPaid")
    loan_payment_event = get_last_event(usdc_loans_peripheral_contract, name="LoanPayment")

    loan_details = usdc_loans_core_contract.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)

    assert usdc_loans_core_contract.getLoanPaid(borrower, loan_id)
    assert (
        usdc_loans_core_contract.getLoanPaidPrincipal(borrower, loan_id)
        + usdc_loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id)
        == payable_amount
    )
    assert loan_details.paid == usdc_loans_core_contract.getLoanPaid(borrower, loan_id)
    assert loan_details.paidPrincipal == usdc_loans_core_contract.getLoanPaidPrincipal(
        borrower, loan_id
    )
    assert loan_details.paidInterestAmount == usdc_loans_core_contract.getLoanPaidInterestAmount(borrower, loan_id)
    assert usdc_loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp")) == 0

    assert loan_paid_event.wallet == borrower
    assert loan_paid_event.loanId == loan_id
    assert loan_payment_event.wallet == borrower
    assert loan_payment_event.loanId == loan_id
    assert loan_payment_event.principal + loan_payment_event.interestAmount == payable_amount

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == borrower

    assert usdc_contract.balanceOf(borrower) + payable_amount == borrower_initial_balance + amount


def test_pay_loan_already_paid(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, sender=borrower)

    (v, r, s) = create_signature()

    loan_id = loans_peripheral_contract.reserveEth(
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

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)

    payable_amount = loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))

    loans_peripheral_contract.pay(loan_id, sender=borrower, value=payable_amount)

    with boa.reverts("loan already paid"):
        loans_peripheral_contract.pay(loan_id, sender=borrower, value=payable_amount)


def test_set_default_loan_wrong_sender(loans_peripheral_contract, investor, borrower):
    with boa.reverts("msg.sender is not the owner"):
        loans_peripheral_contract.settleDefault(borrower, 0, sender=investor)


def test_set_default_loan_not_started(
    loans_peripheral_contract, contract_owner, borrower
):
    with boa.reverts("loan not found"):
        loans_peripheral_contract.settleDefault(borrower, 0, sender=contract_owner)


def test_set_default_loan(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    liquidations_peripheral_contract,
    liquidations_core_contract,
    erc721_contract,
    erc20_contract,
    contract_owner,
    investor,
    borrower,
    test_collaterals,
):
    lending_pool_peripheral_contract.depositEth(sender=investor, value=Web3.to_wei(1, "ether"))

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(
        collateral_vault_core_contract, True, sender=borrower
    )

    maturity = boa.eval("block.timestamp") + 10
    (v, r, s) = create_signature(maturity=maturity)

    loan_id = loans_peripheral_contract.reserveEth(
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

    loan = loans_core_contract.getLoan(borrower, loan_id)
    loan = LoanInfo(*loan)

    boa.env.time_travel(seconds=15)

    print(loans_core_contract.getLoanMaturity(borrower, loan_id))
    print(loans_core_contract.getLoanDefaulted(borrower, loan_id))
    print(boa.eval("block.timestamp"))
    print(loans_peripheral_contract.liquidationsPeripheralContract())
    print(liquidations_peripheral_contract)

    loans_peripheral_contract.settleDefault(borrower, loan_id, sender=contract_owner)

    assert loans_core_contract.getLoanDefaulted(borrower, loan_id)

    for collateral in test_collaterals:
        assert erc721_contract.ownerOf(collateral[1]) == collateral_vault_core_contract.address

        liquidation = liquidations_core_contract.getLiquidation(collateral[0], collateral[1])
        liquidation = Liquidation(*liquidation)

        interest_amount = int(
            Decimal(collateral[2])
            * Decimal(loan.interest * Decimal(loan.maturity - loan.startTime))
            / Decimal(25920000000)
        )
        apr = int(Decimal(LOAN_INTEREST) * Decimal(12))

        assert liquidation.collateralAddress == collateral[0]
        assert liquidation.tokenId == collateral[1]
        assert liquidation.principal == collateral[2]
        assert liquidation.interestAmount == interest_amount
        assert liquidation.apr == apr
        assert liquidation.gracePeriodPrice == Decimal(collateral[2]) + Decimal(
            interest_amount
        ) + int(min(0.025 * collateral[2], Web3.to_wei(0.2, "ether")))
        assert liquidation.lenderPeriodPrice == Decimal(collateral[2]) + Decimal(
            interest_amount
        ) + int(min(0.025 * collateral[2], Web3.to_wei(0.2, "ether")))
        assert liquidation.borrower == borrower
        assert liquidation.erc20TokenContract == erc20_contract.address
        assert not liquidation.inAuction


@given(
    loan_duration=st.integers(min_value=1, max_value=90),
    passed_time=st.integers(min_value=1, max_value=200),
    interest=st.integers(min_value=0, max_value=10000),
)
@settings(max_examples=5, deadline=1500)
def test_payable_amount(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
    loan_duration,
    passed_time,
    interest, contracts_config
):
    amount = LOAN_AMOUNT
    now = int(dt.datetime.now().timestamp())
    maturity = now + loan_duration * 24 * 3600

    lending_pool_peripheral_contract.depositEth(sender=investor, value=amount * 5)

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, sender=borrower)


    (v, r, s) = create_signature(maturity=maturity, interest=interest)

    loan_id = loans_peripheral_contract.reserveEth(
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

    loan_details = loans_core_contract.getLoan(borrower, loan_id)
    loan_details = LoanInfo(*loan_details)
    payable_amount = loans_peripheral_contract.getLoanPayableAmount(borrower, loan_id, boa.eval("block.timestamp"))

    contract_time_passed = boa.eval("block.timestamp") - loan_details.startTime
    loan_duration_in_contract = maturity - loan_details.startTime
    minimum_interest_period = 7*86400

    payable_duration = max(
        minimum_interest_period,
        contract_time_passed + INTEREST_ACCRUAL_PERIOD - contract_time_passed % INTEREST_ACCRUAL_PERIOD
    )
    due_amount = amount * (loan_duration_in_contract * 10000 + interest * payable_duration) // (loan_duration_in_contract * 10000)

    assert payable_amount == due_amount


@given(
    genesis_token=st.integers(min_value=0, max_value=2),
)
@settings(max_examples=5, deadline=1000)
def test_genesis_pass_validation(
    loans_peripheral_contract,
    create_signature,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_core_contract,
    erc721_contract,
    contract_owner,
    borrower,
    investor,
    test_collaterals,
    contracts_config,
    genesis_contract,
    delegation_registry_contract,
    genesis_token,
):
    amount = LOAN_AMOUNT
    now = int(dt.datetime.now().timestamp())
    maturity = now + 7 * 24 * 3600
    interest = 15

    lending_pool_peripheral_contract.depositEth(sender=investor, value=amount * 5)

    for k in range(5):
        erc721_contract.mint(borrower, k, sender=contract_owner)
    erc721_contract.setApprovalForAll(collateral_vault_core_contract, True, sender=borrower)

    print(f"{genesis_token=} {borrower=}")

    if genesis_token > 0:
        genesis_contract.transferFrom(contract_owner, borrower, genesis_token, sender=contract_owner)

    (v, r, s) = create_signature(maturity=maturity, interest=interest, genesis_token=genesis_token)

    loans_peripheral_contract.reserveEth(
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

    event = get_last_event(loans_peripheral_contract, name="LoanCreated")
    assert event.genesisToken == genesis_token
