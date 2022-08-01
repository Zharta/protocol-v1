import pytest
import conftest_base


contract_owner = conftest_base.contract_owner
erc20_contract = conftest_base.erc20_contract


@pytest.fixture(scope="module", autouse=True)
def treasury(accounts):
    yield accounts[4]


@pytest.fixture(scope="module", autouse=True)
def sushi_factory(accounts):
    yield accounts[5]


@pytest.fixture(scope="module", autouse=True)
def setupSushi(accounts):
    pass


# @pytest.fixture(scope="module", autouse=True)
# def setupNFTX(contract_owner):
    
#     staking_token_provider = StakingTokenProvider.deploy({"from": owner})



# staking_token_provider = StakingTokenProvider.deploy({"from": owner})

# staking_token_provider.__StakingTokenProvider_init(sushi_factory, weth, "x", {"from": owner})

# lp_staking = NFTXLPStaking.deploy({"from": owner})

# lp_staking.__NFTXLPStaking__init(staking_token_provider, {"from": owner})

# fee_distributor = NFTXSimpleFeeDistributor.deploy({"from": owner})

# fee_distributor.__SimpleFeeDistributor__init__(lp_staking, treasury, {"from": owner})

# erc721 = ERC721.deploy({"from": owner})

# vault_impl = NFTXVaultUpgradeable.deploy({"from": owner})

# vault_factory = NFTXVaultFactoryUpgradeable.deploy({"from": owner})

# vault_factory.__NFTXVaultFactory_init(vault_impl, fee_distributor, {"from": owner})

# fee_distributor.setNFTXVaultFactory(vault_factory, {"from": owner})

# lp_staking.setNFTXVaultFactory(vault_factory, {"from": owner})

# vault_factory.createVault("zharta_test_vault", "ZTV", erc721, False, True, {"from": owner})

