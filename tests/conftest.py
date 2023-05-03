from datetime import datetime as dt
from web3 import Web3
import brownie
from brownie import Contract
from brownie.exceptions import ContractNotFound

import conftest_base
import pytest
import json


MATURITY = int(dt.now().timestamp()) + 30 * 24 * 60 * 60
LOAN_AMOUNT = Web3.toWei(0.1, "ether")
LOAN_INTEREST = 250  # 2.5% in parts per 10000
INTEREST_ACCRUAL_PERIOD = 24 * 60 * 60

PROTOCOL_FEES_SHARE = 2500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_CAPITAL_EFFICIENCY = 7000 # parts per 10000, e.g. 2.5% is 250 parts per 10000

GRACE_PERIOD_DURATION = 50 # 2 days
LENDER_PERIOD_DURATION = 50 # 15 days
AUCTION_DURATION = 50 # 15 days

MAX_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
MAX_LOANS_POOL_SHARE = 1500 # parts per 10000, e.g. 2.5% is 250 parts per 10000
LOCK_PERIOD_DURATION = 7 * 24 * 60 * 60


contract_owner = conftest_base.contract_owner
not_contract_owner = conftest_base.not_contract_owner
investor = conftest_base.investor
borrower = conftest_base.borrower
protocol_wallet = conftest_base.protocol_wallet
erc20_contract = conftest_base.erc20_contract
erc721_contract = conftest_base.erc721_contract
usdc_contract = conftest_base.usdc_contract



@pytest.fixture(scope="module", autouse=True)
def cryptopunks_market_contract(contract_owner):
    abi = """ [
        {"constant":true,"inputs":[{"name":"","type":"uint256"}],"name":"punkIndexToAddress","outputs":[{"name":"","type":"address"}],"payable":false,"type":"function"},
        {"constant":false,"inputs":[{"name":"to","type":"address"},{"name":"punkIndex","type":"uint256"}],"name":"transferPunk","outputs":[],"payable":false,"type":"function"},
        {"constant":false,"inputs":[{"name":"punkIndex","type":"uint256"},{"name":"minSalePriceInWei","type":"uint256"},{"name":"toAddress","type":"address"}],"name":"offerPunkForSaleToAddress","outputs":[],"payable":false,"type":"function"}
    ] """
    try:
        return Contract.from_abi(
            "Cryptopunks",
            "0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB",
            json.loads(abi),
            owner=contract_owner
        )
    except ContractNotFound:
        return None


@pytest.fixture(scope="module", autouse=True)
def wpunks_contract(ERC721, contract_owner):
    abi = """ [
        {"constant":false,"inputs":[{"internalType":"uint256","name":"punkIndex","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
        {"constant":false,"inputs":[],"name":"registerProxy","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
        {"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
        {"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},
        {"constant":true,"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},
        {"constant":true,"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"proxyInfo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}
    ] """
    try:
        return Contract.from_abi(
            "WrappedPunk",
            "0xb7F7F6C52F2e2fdb1963Eab30438024864c313F6",
            json.loads(abi),
            owner=contract_owner
        )
    except ContractNotFound:
        return None


@pytest.fixture(scope="module", autouse=True)
def hashmasks_contract(ERC721, contract_owner):
    try:
        return ERC721.at("0xC2C747E0F7004F9E8817Db2ca4997657a7746928")
    except ContractNotFound:
        return None


@pytest.fixture(scope="module", autouse=True)
def cryptopunks_vault_core_contract(CryptoPunksVaultCore, cryptopunks_market_contract, delegation_registry_contract, contract_owner):
    cryptopunks_address = cryptopunks_market_contract.address if cryptopunks_market_contract else brownie.ZERO_ADDRESS
    return CryptoPunksVaultCore.deploy(cryptopunks_address, delegation_registry_contract, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def delegation_registry_contract(ERC721, contract_owner):
    abi = """ [
      {
        "inputs": [
          {"internalType": "address", "name": "delegate", "type": "address"},
          {"internalType": "address", "name": "vault", "type": "address"},
          {"internalType": "address", "name": "contract_", "type": "address"},
          {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "checkDelegateForToken",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
      },
      {
        "inputs": [
          {"internalType": "address", "name": "delegate", "type": "address"},
          {"internalType": "address", "name": "contract_", "type": "address"},
          {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
          {"internalType": "bool", "name": "value", "type": "bool"}
        ],
        "name": "delegateForToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
      }
    ] """
    try:
        return Contract.from_abi(
            "DelegationRegistry",
            "0x00000000000076A84feF008CDAbe6409d2FE638B",
            json.loads(abi),
            owner=contract_owner
        )
    except ContractNotFound:
        return None


@pytest.fixture(scope="module")
def genesis_contract(GenesisPass, contract_owner):
    yield GenesisPass.deploy(contract_owner, {"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def collateral_vault_core_contract(CollateralVaultCoreV2, contract_owner, delegation_registry_contract):
    yield CollateralVaultCoreV2.deploy(delegation_registry_contract, {"from": contract_owner})

@pytest.fixture(scope="module", autouse=True)
def collateral_vault_peripheral_contract(
    CollateralVaultPeripheral,
    collateral_vault_core_contract,
    contract_owner
):
    yield CollateralVaultPeripheral.deploy(
        collateral_vault_core_contract,
        {"from": contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def usdc_loans_core_contract(LoansCore, contract_owner):
    yield LoansCore.deploy({'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def lending_pool_core_contract(LendingPoolCore, erc20_contract, contract_owner):
    yield LendingPoolCore.deploy(erc20_contract, {'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def usdc_lending_pool_core_contract(LendingPoolCore, usdc_contract, contract_owner):
    yield LendingPoolCore.deploy(usdc_contract, {'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def lending_pool_lock_contract(LendingPoolLock, erc20_contract, contract_owner):
    yield LendingPoolLock.deploy(erc20_contract, {'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def usdc_lending_pool_lock_contract(LendingPoolLock, usdc_contract, contract_owner):
    yield LendingPoolLock.deploy(usdc_contract, {'from': contract_owner})


@pytest.fixture(scope="module", autouse=True)
def lending_pool_peripheral_contract(LendingPoolPeripheral, lending_pool_core_contract, lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def usdc_lending_pool_peripheral_contract(
    LendingPoolPeripheral,
    usdc_lending_pool_core_contract,
    usdc_lending_pool_lock_contract,
    usdc_contract,
    contract_owner,
    protocol_wallet
):
    yield LendingPoolPeripheral.deploy(
        usdc_lending_pool_core_contract,
        usdc_lending_pool_lock_contract,
        usdc_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def lending_pool_peripheral_contract_aux(LendingPoolPeripheral, lending_pool_core_contract, lending_pool_lock_contract, erc20_contract, contract_owner, protocol_wallet):
    yield LendingPoolPeripheral.deploy(
        lending_pool_core_contract,
        lending_pool_lock_contract,
        erc20_contract,
        protocol_wallet,
        PROTOCOL_FEES_SHARE,
        MAX_CAPITAL_EFFICIENCY,
        False,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def loans_peripheral_contract(
    Loans,
    loans_core_contract,
    lending_pool_peripheral_contract,
    collateral_vault_peripheral_contract,
    genesis_contract,
    delegation_registry_contract,
    contract_owner
):
    yield Loans.deploy(
        INTEREST_ACCRUAL_PERIOD,
        loans_core_contract,
        lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def usdc_loans_peripheral_contract(
    Loans,
    usdc_loans_core_contract,
    usdc_lending_pool_peripheral_contract,
    collateral_vault_peripheral_contract,
    genesis_contract,
    delegation_registry_contract,
    contract_owner
):
    yield Loans.deploy(
        INTEREST_ACCRUAL_PERIOD,
        usdc_loans_core_contract,
        usdc_lending_pool_peripheral_contract,
        collateral_vault_peripheral_contract,
        genesis_contract,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def loans_peripheral_contract_aux(Loans, lending_pool_peripheral_contract, contract_owner, accounts, genesis_contract, delegation_registry_contract):
    yield Loans.deploy(
        INTEREST_ACCRUAL_PERIOD,
        accounts[4],
        lending_pool_peripheral_contract,
        accounts[5],
        genesis_contract,
        {'from': contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def liquidations_core_contract(LiquidationsCore, contract_owner):
    return LiquidationsCore.deploy({"from": contract_owner})


@pytest.fixture(scope="module", autouse=True)
def sushi_router_contract(contract_owner):
    abi = """ [
    {
        "inputs": [
          {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
          {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
          {"internalType": "address[]", "name": "path", "type": "address[]"},
          {"internalType": "address", "name": "to", "type": "address"},
          {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [
          {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
      }
    ] """
    return Contract.from_abi(
        "SushiRouter",
        "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        json.loads(abi),
        owner=contract_owner
    )


@pytest.fixture(scope="module", autouse=True)
def liquidations_peripheral_contract(LiquidationsPeripheral, liquidations_core_contract, erc20_contract, contract_owner):
    liquidations_peripheral_contract = LiquidationsPeripheral.deploy(
        liquidations_core_contract,
        GRACE_PERIOD_DURATION,
        LENDER_PERIOD_DURATION,
        AUCTION_DURATION,
        erc20_contract,
        {"from": contract_owner}
    )
    liquidations_peripheral_contract.setNFTXVaultFactoryAddress("0xBE86f647b167567525cCAAfcd6f881F1Ee558216", {"from": contract_owner})
    liquidations_peripheral_contract.setNFTXMarketplaceZapAddress("0x0fc584529a2AEfA997697FAfAcbA5831faC0c22d", {"from": contract_owner})
    liquidations_peripheral_contract.setSushiRouterAddress("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F", {"from": contract_owner})
    return liquidations_peripheral_contract


@pytest.fixture(scope="module", autouse=True)
def liquidity_controls_contract(LiquidityControls, contract_owner):
    yield LiquidityControls.deploy(
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
        {"from": contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def usdc_liquidity_controls_contract(LiquidityControls, contract_owner):
    yield LiquidityControls.deploy(
        False,
        MAX_POOL_SHARE,
        False,
        LOCK_PERIOD_DURATION,
        False,
        MAX_LOANS_POOL_SHARE,
        False,
        {"from": contract_owner}
    )


@pytest.fixture(scope="module", autouse=True)
def test_collaterals(erc721_contract):
    result = []
    for k in range(5):
        result.append((erc721_contract.address, k, LOAN_AMOUNT / 5))
    yield result


@pytest.fixture(scope="module", autouse=True)
def cryptopunk_collaterals(cryptopunks_market_contract, borrower):
    result = []
    if cryptopunks_market_contract is None:
        return result
    for k in range(5):
        owner = cryptopunks_market_contract.punkIndexToAddress(k)
        brownie.network.rpc.unlock_account(owner)
        cryptopunks_market_contract.transferPunk(borrower, k, {'from': owner})
        result.append((cryptopunks_market_contract, k, LOAN_AMOUNT // 5))
    return result


@pytest.fixture(scope="module")
def contracts_config(
    collateral_vault_core_contract,
    collateral_vault_peripheral_contract,
    contract_owner,
    cryptopunks_market_contract,
    cryptopunks_vault_core_contract,
    erc20_contract,
    lending_pool_core_contract,
    lending_pool_lock_contract,
    lending_pool_peripheral_contract,
    liquidations_core_contract,
    liquidations_peripheral_contract,
    liquidity_controls_contract,
    loans_core_contract,
    loans_peripheral_contract,
    wpunks_contract,
):
    collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(erc20_contract, loans_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    lending_pool_core_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_lock_contract.setLendingPoolPeripheralAddress(lending_pool_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})
    lending_pool_peripheral_contract.setLoansPeripheralAddress(loans_peripheral_contract, {"from": contract_owner})
    liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(erc20_contract, lending_pool_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(erc20_contract, loans_core_contract, {"from": contract_owner})
    liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    loans_core_contract.setLoansPeripheral(loans_peripheral_contract, {"from": contract_owner})
    loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    loans_peripheral_contract.setLiquidityControlsAddress(liquidity_controls_contract, {"from": contract_owner})
    if cryptopunks_market_contract is not None:
        collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract, {"from": contract_owner})
        liquidations_peripheral_contract.setCryptoPunksAddress(cryptopunks_market_contract, {"from": contract_owner})
    if wpunks_contract is not None:
        liquidations_peripheral_contract.setWrappedPunksAddress(wpunks_contract, {"from": contract_owner})


@pytest.fixture(scope="module")
def usdc_contracts_config(
    contracts_config,
    # collateral_vault_core_contract,
    collateral_vault_peripheral_contract,
    contract_owner,
    # cryptopunks_market_contract,
    # cryptopunks_vault_core_contract,
    usdc_contract,
    usdc_lending_pool_core_contract,
    usdc_lending_pool_lock_contract,
    usdc_lending_pool_peripheral_contract,
    liquidations_core_contract,
    liquidations_peripheral_contract,
    usdc_liquidity_controls_contract,
    usdc_loans_core_contract,
    usdc_loans_peripheral_contract,
    # wpunks_contract,
):
    # collateral_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    collateral_vault_peripheral_contract.addLoansPeripheralAddress(usdc_contract, usdc_loans_peripheral_contract, {"from": contract_owner})
    # collateral_vault_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    # cryptopunks_vault_core_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    usdc_lending_pool_core_contract.setLendingPoolPeripheralAddress(usdc_lending_pool_peripheral_contract, {"from": contract_owner})
    usdc_lending_pool_lock_contract.setLendingPoolPeripheralAddress(usdc_lending_pool_peripheral_contract, {"from": contract_owner})
    usdc_lending_pool_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    usdc_lending_pool_peripheral_contract.setLiquidityControlsAddress(usdc_liquidity_controls_contract, {"from": contract_owner})
    usdc_lending_pool_peripheral_contract.setLoansPeripheralAddress(usdc_loans_peripheral_contract, {"from": contract_owner})
    # liquidations_core_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLendingPoolPeripheralAddress(usdc_contract, usdc_lending_pool_peripheral_contract, {"from": contract_owner})
    liquidations_peripheral_contract.addLoansCoreAddress(usdc_contract, usdc_loans_core_contract, {"from": contract_owner})
    # liquidations_peripheral_contract.setCollateralVaultPeripheralAddress(collateral_vault_peripheral_contract, {"from": contract_owner})
    usdc_loans_core_contract.setLoansPeripheral(usdc_loans_peripheral_contract, {"from": contract_owner})
    usdc_loans_peripheral_contract.setLiquidationsPeripheralAddress(liquidations_peripheral_contract, {"from": contract_owner})
    usdc_loans_peripheral_contract.setLiquidityControlsAddress(usdc_liquidity_controls_contract, {"from": contract_owner})
    # if cryptopunks_market_contract is not None:
    #     collateral_vault_peripheral_contract.addVault(cryptopunks_market_contract, cryptopunks_vault_core_contract, {"from": contract_owner})
    #     liquidations_peripheral_contract.setCryptoPunksAddress(cryptopunks_market_contract, {"from": contract_owner})
    # if wpunks_contract is not None:
    #     liquidations_peripheral_contract.setWrappedPunksAddress(wpunks_contract, {"from": contract_owner})


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
