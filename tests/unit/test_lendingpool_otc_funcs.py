import boa
import pytest

from ..conftest_base import ZERO_ADDRESS, get_last_event

DEPLOYER = boa.env.generate_address()
LENDER = boa.env.generate_address()

PROTOCOL_WALLET = boa.env.generate_address()
PROTOCOL_FEE = 100  # bps


@pytest.fixture(scope="module")
def weth9_contract():
    return boa.load_partial("contracts/auxiliary/token/WETH9Mock.vy")


@pytest.fixture(scope="module")
def erc20_token(weth9_contract):
    with boa.env.prank(DEPLOYER):
        contract = weth9_contract.deploy("ERC20", "ERC20", 18, 10**20)
        boa.env.set_balance(contract.address, 10**20)
        return contract


@pytest.fixture(scope="module")
def weth_pool(lendingpool_eth_otc_contract, erc20_token):
    with boa.env.prank(DEPLOYER):
        contract = lendingpool_eth_otc_contract.deploy(erc20_token.address)
        proxy_address = contract.create_proxy(PROTOCOL_WALLET, PROTOCOL_FEE, LENDER)
        proxy = lendingpool_eth_otc_contract.at(proxy_address)
        proxy.setLoansPeripheralAddress(boa.env.generate_address())
        proxy.setLiquidationsPeripheralAddress(boa.env.generate_address())
        return proxy


@pytest.fixture(scope="module")
def erc20_pool(lendingpool_erc20_otc_contract, erc20_token):
    with boa.env.prank(DEPLOYER):
        contract = lendingpool_erc20_otc_contract.deploy(erc20_token.address)
        proxy_address = contract.create_proxy(PROTOCOL_WALLET, PROTOCOL_FEE, LENDER)
        proxy = lendingpool_erc20_otc_contract.at(proxy_address)
        proxy.setLoansPeripheralAddress(boa.env.generate_address())
        proxy.setLiquidationsPeripheralAddress(boa.env.generate_address())
        return proxy


def test_deposit_eth_fail(erc20_pool, weth_pool):

    amount = 10**18
    account1 = boa.env.generate_address()
    boa.env.set_balance(LENDER, amount)
    boa.env.set_balance(account1, amount)

    # pool not allowing eth
    with boa.reverts():
        erc20_pool.depositEth(value=amount, sender=LENDER)
    assert erc20_pool.totalAmountDeposited(LENDER) == 0

    # account not lender
    with boa.reverts():
        weth_pool.depositEth(value=amount, sender=account1)

    # zero eth sent
    with boa.reverts():
        weth_pool.depositEth(value=0, sender=LENDER)

    # pool not active
    weth_pool.changePoolStatus(False, sender=DEPLOYER)
    with boa.reverts():
        weth_pool.depositEth(value=amount, sender=LENDER)
    weth_pool.changePoolStatus(True, sender=DEPLOYER)
    assert weth_pool.totalAmountDeposited(LENDER) == 0

    assert weth_pool.fundsAvailable() == 0


def test_deposit_eth_success(erc20_pool, weth_pool, erc20_token):

    amount = 10**18
    boa.env.set_balance(LENDER, amount)

    weth_pool.depositEth(value=amount, sender=LENDER)
    event = get_last_event(weth_pool, name="Deposit")

    assert weth_pool.fundsAvailable() == amount

    assert event.walletIndexed == LENDER
    assert event.wallet == LENDER
    assert event.amount == amount
    assert event.erc20TokenContract == weth_pool.erc20TokenContract()

    assert boa.env.get_balance(LENDER) == 0

    assert erc20_token.balanceOf(weth_pool.address) == amount

    currentAmountDeposited, totalAmountDeposited, _, _, _ = weth_pool.poolFunds()
    assert totalAmountDeposited == amount
    assert currentAmountDeposited == amount


def test_deposit_erc20_fail(erc20_pool, weth9_contract):

    amount = 10**18
    account1 = boa.env.generate_address()
    erc20_token = weth9_contract.at(erc20_pool.erc20TokenContract())
    for address in [LENDER, account1]:
        erc20_token.eval(f"self.balanceOf[{address}] = {amount}")

    # account not lender
    erc20_token.approve(erc20_pool.address, amount, sender=account1)
    with boa.reverts():
        erc20_pool.deposit(amount, sender=account1)

    with boa.env.prank(LENDER):

        # not enough funds allowed
        erc20_token.approve(erc20_pool.address, amount - 1)
        with boa.reverts():
            erc20_pool.deposit(amount)
        assert erc20_pool.totalAmountDeposited(LENDER) == 0

        # zero eth sent
        with boa.reverts():
            erc20_pool.deposit(0)

        # pool not active
        erc20_token.approve(erc20_pool.address, amount)
        erc20_pool.changePoolStatus(False, sender=DEPLOYER)
        with boa.reverts():
            erc20_pool.deposit(amount)
        erc20_pool.changePoolStatus(True, sender=DEPLOYER)
        assert erc20_pool.totalAmountDeposited(LENDER) == 0

        assert erc20_pool.fundsAvailable() == 0


def test_deposit_erc20_success(erc20_pool, erc20_token):

    amount = 10**18
    erc20_token.eval(f"self.balanceOf[{LENDER}] = {amount}")

    with boa.env.prank(LENDER):
        erc20_token.approve(erc20_pool.address, amount)
        erc20_pool.deposit(amount)
        event = get_last_event(erc20_pool, name="Deposit")

    assert erc20_pool.fundsAvailable() == amount

    assert event.walletIndexed == LENDER
    assert event.wallet == LENDER
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()

    assert erc20_token.balanceOf(LENDER) == 0
    assert erc20_token.balanceOf(erc20_pool.address) == amount

    currentAmountDeposited, totalAmountDeposited, _, _, _ = erc20_pool.poolFunds()
    assert totalAmountDeposited == amount
    assert currentAmountDeposited == amount


def test_withdraw_eth_fail(erc20_pool, weth_pool, erc20_token):

    amount = 10**18
    account1 = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{erc20_pool.address}] = {amount}")
    erc20_token.eval(f"self.balanceOf[{weth_pool.address}] = {amount}")

    erc20_pool.eval(f"self.fundsAvailable = {amount}")

    # pool not allowing eth
    with boa.reverts():
        erc20_pool.withdrawEth(amount, sender=LENDER)

    # account not lender
    with boa.reverts():
        weth_pool.withdrawEth(amount, sender=account1)

    # zero eth sent
    with boa.reverts():
        weth_pool.withdrawEth(0, sender=LENDER)

    # not engough funds available
    weth_pool.eval(f"self.fundsAvailable = {amount-1}")
    with boa.reverts():
        weth_pool.withdrawEth(amount, sender=LENDER)


def test_withdraw_eth_success(weth_pool, erc20_token):

    amount = 10**18
    erc20_token.eval(f"self.balanceOf[{weth_pool.address}] = {amount}")

    weth_pool.eval(f"self.fundsAvailable = {amount}")
    weth_pool.eval(f"self.poolFunds.totalAmountDeposited = {amount}")
    weth_pool.eval(f"self.poolFunds.currentAmountDeposited = {amount}")

    weth_pool.withdrawEth(amount, sender=LENDER)
    event = get_last_event(weth_pool, name="Withdrawal")

    assert weth_pool.fundsAvailable() == 0

    currentAmountDeposited, totalAmountDeposited, totalAmountWithdrawn, _, _ = weth_pool.poolFunds()
    assert totalAmountDeposited == amount
    assert currentAmountDeposited == 0
    assert totalAmountWithdrawn == amount

    assert event.walletIndexed == LENDER
    assert event.wallet == LENDER
    assert event.amount == amount
    assert event.erc20TokenContract == weth_pool.erc20TokenContract()

    assert boa.env.get_balance(LENDER) == amount

    assert erc20_token.balanceOf(weth_pool.address) == 0


def test_withdraw_erc20_fail(erc20_pool, erc20_token):

    amount = 10**18
    account1 = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{erc20_pool.address}] = {amount}")
    erc20_pool.eval(f"self.fundsAvailable = {amount}")

    # account not lender
    with boa.reverts():
        erc20_pool.withdraw(amount, sender=account1)

    # zero eth requested
    with boa.reverts():
        erc20_pool.withdraw(0, sender=LENDER)

    # not enough funds available
    erc20_pool.eval(f"self.fundsAvailable = {amount-1}")
    with boa.reverts():
        erc20_pool.withdraw(amount, sender=LENDER)


def test_withdraw_erc20_success(erc20_pool, erc20_token):

    amount = 10**18
    erc20_token.eval(f"self.balanceOf[{erc20_pool.address}] = {amount}")

    erc20_pool.eval(f"self.fundsAvailable = {amount}")
    erc20_pool.eval(f"self.poolFunds.totalAmountDeposited = {amount}")
    erc20_pool.eval(f"self.poolFunds.currentAmountDeposited = {amount}")

    erc20_pool.withdraw(amount, sender=LENDER)
    event = get_last_event(erc20_pool, name="Withdrawal")

    assert erc20_pool.fundsAvailable() == 0

    currentAmountDeposited, totalAmountDeposited, totalAmountWithdrawn, _, _ = erc20_pool.poolFunds()
    assert totalAmountDeposited == amount
    assert currentAmountDeposited == 0
    assert totalAmountWithdrawn == amount

    assert event.walletIndexed == LENDER
    assert event.wallet == LENDER
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()

    assert erc20_token.balanceOf(LENDER) == amount
    assert erc20_token.balanceOf(erc20_pool.address) == 0


def test_send_funds_fail(erc20_pool, erc20_token):

    amount = 10**18
    wallet = boa.env.generate_address()
    loans = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{erc20_pool.address}] = {amount}")
    erc20_pool.eval(f"self.fundsAvailable = {amount}")

    # account not lender
    with boa.reverts():
        erc20_pool.sendFunds(wallet, amount, sender=wallet)

    # zero amount sent
    with boa.reverts():
        erc20_pool.sendFunds(wallet, 0, sender=loans)

    # not enough funds available
    erc20_pool.eval(f"self.fundsAvailable = {amount-1}")
    with boa.reverts():
        erc20_pool.sendFunds(wallet, amount, sender=loans)


def test_send_funds_success(erc20_pool, erc20_token):

    amount = 10**18
    wallet = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{erc20_pool.address}] = {amount}")
    erc20_pool.eval(f"self.fundsAvailable = {amount}")

    erc20_pool.sendFunds(wallet, amount, sender=erc20_pool.loansContract())
    event = get_last_event(erc20_pool, name="FundsTransfer")

    assert erc20_pool.fundsAvailable() == 0
    assert event.walletIndexed == wallet
    assert event.wallet == wallet
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()

    assert erc20_token.balanceOf(wallet) == amount
    assert erc20_token.balanceOf(erc20_pool.address) == 0


def test_send_funds_eth_fail(weth_pool):

    amount = 10**18
    wallet = boa.env.generate_address()

    boa.env.set_balance(weth_pool.address, amount)
    weth_pool.eval(f"self.fundsAvailable = {amount}")

    # account not lender
    with boa.reverts():
        weth_pool.sendFundsEth(wallet, amount, sender=wallet)

    # zero amount sent
    with boa.reverts():
        weth_pool.sendFundsEth(wallet, 0, sender=weth_pool.loansContract())

    # not enough funds available
    weth_pool.eval(f"self.fundsAvailable = {amount-1}")
    with boa.reverts():
        weth_pool.sendFundsEth(wallet, amount, sender=weth_pool.loansContract())


def test_send_funds_eth_success(weth_pool, erc20_token):

    amount = 10**18
    wallet = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{weth_pool.address}] = {amount}")
    weth_pool.eval(f"self.fundsAvailable = {amount}")

    weth_pool.sendFundsEth(wallet, amount, sender=weth_pool.loansContract())

    event = get_last_event(weth_pool, name="FundsTransfer")
    assert event.walletIndexed == wallet
    assert event.wallet == wallet
    assert event.amount == amount
    assert event.erc20TokenContract == weth_pool.erc20TokenContract()

    assert weth_pool.fundsAvailable() == 0
    assert boa.env.get_balance(wallet) == amount
    assert boa.env.get_balance(weth_pool.address) == 0


def test_receive_funds_eth_fail(weth_pool):

    amount = 10**18
    pool_rewards = 10**17
    borrower = boa.env.generate_address()

    loans = weth_pool.loansContract()
    boa.env.set_balance(loans, amount + pool_rewards)
    weth_pool.eval(f"self.fundsInvested = {amount}")

    # sender not loans
    boa.env.set_balance(borrower, amount + pool_rewards)
    with boa.reverts():
        weth_pool.receiveFundsEth(borrower, amount, pool_rewards, value=amount + pool_rewards, sender=borrower)

    # zero amount
    with boa.reverts():
        weth_pool.receiveFundsEth(borrower, 0, 0, value=amount + pool_rewards, sender=loans)

    # not enough funds
    with boa.reverts():
        weth_pool.receiveFundsEth(borrower, amount, pool_rewards, value=amount + pool_rewards - 1, sender=loans)

    # amount gt invested
    with boa.reverts():
        weth_pool.receiveFundsEth(borrower, amount + 1, 0, value=amount + pool_rewards, sender=loans)


def test_receive_funds_eth_success(weth_pool, erc20_token):

    amount = 10**18
    pool_rewards = 10**17
    protocol_rewards = pool_rewards * weth_pool.protocolFeesShare() // 10000
    borrower = boa.env.generate_address()

    loans = weth_pool.loansContract()
    boa.env.set_balance(loans, amount + pool_rewards)
    weth_pool.eval(f"self.fundsInvested = {amount}")

    weth_pool.receiveFundsEth(borrower, amount, pool_rewards, value=amount + pool_rewards, sender=loans)

    event = get_last_event(weth_pool, name="FundsReceipt")
    assert event.walletIndexed == borrower
    assert event.wallet == borrower
    assert event.amount == amount
    assert event.rewardsPool == pool_rewards - protocol_rewards
    assert event.rewardsProtocol == protocol_rewards
    assert event.investedAmount == amount
    assert event.erc20TokenContract == weth_pool.erc20TokenContract()
    assert event.fundsOrigin == "loan"

    assert weth_pool.fundsAvailable() == amount + pool_rewards - protocol_rewards

    assert boa.env.get_balance(loans) == 0
    assert erc20_token.balanceOf(weth_pool.address) == amount + pool_rewards - protocol_rewards
    assert erc20_token.balanceOf(weth_pool.protocolWallet()) == protocol_rewards


def test_receive_funds_fail(erc20_pool, erc20_token):

    amount = 10**18
    pool_rewards = 10**17
    borrower = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{borrower}] = {amount + pool_rewards}")
    erc20_pool.eval(f"self.fundsInvested = {amount}")

    erc20_token.approve(erc20_pool.address, amount + pool_rewards, sender=borrower)

    # sender not loans
    with boa.reverts():
        erc20_pool.receiveFunds(borrower, amount, pool_rewards, sender=borrower)

    # zero amount
    with boa.reverts():
        erc20_pool.receiveFunds(borrower, 0, 0, sender=erc20_pool.loansContract())

    # not approved
    erc20_token.approve(erc20_pool.address, amount + pool_rewards - 1, sender=borrower)
    with boa.reverts():
        erc20_pool.receiveFunds(borrower, amount, pool_rewards, sender=erc20_pool.loansContract())
    erc20_token.approve(erc20_pool.address, amount + pool_rewards, sender=borrower)

    # amount gt invested
    with boa.reverts():
        erc20_pool.receiveFunds(borrower, amount + 1, 0, sender=erc20_pool.loansContract())


def test_receive_funds_success(erc20_pool, erc20_token):

    amount = 10**18
    pool_rewards = 10**17
    protocol_rewards = pool_rewards * erc20_pool.protocolFeesShare() // 10000
    borrower = boa.env.generate_address()

    erc20_token.eval(f"self.balanceOf[{borrower}] = {amount + pool_rewards}")
    erc20_pool.eval(f"self.fundsInvested = {amount}")

    erc20_token.approve(erc20_pool.address, amount + pool_rewards, sender=borrower)
    erc20_pool.receiveFunds(borrower, amount, pool_rewards, sender=erc20_pool.loansContract())

    event = get_last_event(erc20_pool, name="FundsReceipt")
    assert event.walletIndexed == borrower
    assert event.wallet == borrower
    assert event.amount == amount
    assert event.rewardsPool == pool_rewards - protocol_rewards
    assert event.rewardsProtocol == protocol_rewards
    assert event.investedAmount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()
    assert event.fundsOrigin == "loan"

    assert erc20_pool.fundsAvailable() == amount + pool_rewards - protocol_rewards
    assert erc20_token.balanceOf(borrower) == 0
    assert erc20_token.balanceOf(erc20_pool.address) == amount + pool_rewards - protocol_rewards
    assert erc20_token.balanceOf(erc20_pool.protocolWallet()) == protocol_rewards


def test_receive_collateral_from_liquidation_fail(erc20_pool, erc20_token):

    amount = 10**18
    borrower = boa.env.generate_address()
    liquidationsPeripheralContract = erc20_pool.liquidationsPeripheralContract()
    erc20_pool.eval(f"self.fundsInvested = {amount}")

    # msg.sender is not the BN addr
    with boa.reverts():
        erc20_pool.receiveCollateralFromLiquidation(borrower, amount, "origin", sender=borrower)

    # borrower is the zero address
    with boa.reverts():
        erc20_pool.receiveCollateralFromLiquidation(ZERO_ADDRESS, amount, "origin", sender=liquidationsPeripheralContract)

    # amount should be higher than 0
    with boa.reverts():
        erc20_pool.receiveCollateralFromLiquidation(borrower, 0, "origin", sender=liquidationsPeripheralContract)

    # amount more than invested
    with boa.reverts():
        erc20_pool.receiveCollateralFromLiquidation(borrower, amount + 1, "origin", sender=liquidationsPeripheralContract)


def test_receive_collateral_from_liquidation_success(erc20_pool, erc20_token):

    amount = 10**18
    borrower = boa.env.generate_address()
    liquidationsPeripheralContract = erc20_pool.liquidationsPeripheralContract()
    erc20_pool.eval(f"self.fundsInvested = {amount}")

    erc20_pool.receiveCollateralFromLiquidation(borrower, amount, "origin", sender=liquidationsPeripheralContract)

    event = get_last_event(erc20_pool, name="CollateralClaimReceipt")
    assert event.walletIndexed == borrower
    assert event.wallet == borrower
    assert event.amount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()
    assert event.fundsOrigin == "origin"

    assert erc20_pool.fundsInvested() == 0
    assert erc20_pool.fundsAvailable() == 0
    assert erc20_pool.totalRewards() == 0
    assert erc20_pool.collateralClaimsValue() == amount


def test_receive_funds_from_liquidation_fail(erc20_pool, erc20_token):

    amount = 10**18
    rewardsAmount = 10**17
    borrower = boa.env.generate_address()
    liquidations = erc20_pool.liquidationsPeripheralContract()
    erc20_token.eval(f"self.balanceOf[{borrower}] = {amount + rewardsAmount}")

    # borrower is the zero addr
    with boa.reverts():
        erc20_pool.receiveFundsFromLiquidation(ZERO_ADDRESS, amount, rewardsAmount, True, "origin", sender=liquidations)

    # insufficient liquidity
    with boa.reverts():
        erc20_pool.receiveFundsFromLiquidation(borrower, amount, rewardsAmount, True, "origin", sender=liquidations)

    erc20_token.approve(erc20_pool.address, amount + rewardsAmount, sender=borrower)

    # amount should be higher than 0
    with boa.reverts():
        erc20_pool.receiveFundsFromLiquidation(borrower, 0, 0, True, "origin", sender=borrower)


    # msg.sender not liquidations
    with boa.reverts():
        erc20_pool.receiveFundsFromLiquidation(borrower, amount, rewardsAmount, True, "origin", sender=borrower)


def test_receive_funds_from_liquidation_success(erc20_pool, erc20_token):

    amount = 10**18
    rewardsAmount = 10**17
    protocol_rewards = rewardsAmount * erc20_pool.protocolFeesShare() // 10000
    borrower = boa.env.generate_address()
    liquidations = erc20_pool.liquidationsPeripheralContract()

    erc20_token.eval(f"self.balanceOf[{borrower}] = {amount + rewardsAmount}")
    erc20_token.approve(erc20_pool.address, amount + rewardsAmount, sender=borrower)
    erc20_pool.eval(f"self.fundsInvested = {amount}")

    erc20_pool.receiveFundsFromLiquidation(borrower, amount, rewardsAmount, True, "origin", sender=liquidations)

    event = get_last_event(erc20_pool, name="FundsReceipt")
    assert event.walletIndexed == borrower
    assert event.wallet == borrower
    assert event.amount == amount
    assert event.rewardsPool == rewardsAmount - protocol_rewards
    assert event.rewardsProtocol == protocol_rewards
    assert event.investedAmount == amount
    assert event.erc20TokenContract == erc20_pool.erc20TokenContract()
    assert event.fundsOrigin == "origin"

    assert erc20_pool.fundsInvested() == 0
    assert erc20_pool.fundsAvailable() == amount + rewardsAmount - protocol_rewards
    assert erc20_pool.totalRewards() == rewardsAmount - protocol_rewards
    assert erc20_pool.collateralClaimsValue() == 0


def test_receive_funds_from_liquidation_eth_fail(weth_pool, erc20_token):

    amount = 10**18
    rewardsAmount = 10**17
    borrower = boa.env.generate_address()
    boa.env.set_balance(borrower, amount + rewardsAmount)

    # allowEth is False
    with boa.reverts():
        weth_pool.receiveFundsFromLiquidationEth(borrower, amount, rewardsAmount, True, "origin", value=amount+rewardsAmount, sender=borrower)

    # recv amount not match partials
    with boa.reverts():
        weth_pool.receiveFundsFromLiquidationEth(borrower, amount, rewardsAmount, True, "origin", value=amount, sender=borrower)


def test_receive_funds_from_liquidation_eth_success(weth_pool, erc20_token):

    amount = 10**18
    rewardsAmount = 10**17
    protocol_rewards = rewardsAmount * weth_pool.protocolFeesShare() // 10000
    borrower = boa.env.generate_address()
    liquidations = weth_pool.liquidationsPeripheralContract()

    boa.env.set_balance(liquidations, amount + rewardsAmount)
    weth_pool.eval(f"self.fundsInvested = {amount}")

    weth_pool.receiveFundsFromLiquidationEth(borrower, amount, rewardsAmount, True, "origin", value=amount+rewardsAmount, sender=liquidations)

    event = get_last_event(weth_pool, name="FundsReceipt")
    assert event.walletIndexed == borrower
    assert event.wallet == borrower
    assert event.amount == amount
    assert event.rewardsPool == rewardsAmount - protocol_rewards
    assert event.rewardsProtocol == protocol_rewards
    assert event.investedAmount == amount
    assert event.erc20TokenContract == weth_pool.erc20TokenContract()
    assert event.fundsOrigin == "origin"

    assert weth_pool.fundsInvested() == 0
    assert weth_pool.fundsAvailable() == amount + rewardsAmount - protocol_rewards
    assert weth_pool.totalRewards() == rewardsAmount - protocol_rewards
    assert weth_pool.collateralClaimsValue() == 0
