import os
from scripts.deployment import DeploymentManager, Environment

ENV = Environment[os.environ.get("ENV", "local")]

def ape_init_extras(network):
    dm = DeploymentManager(ENV)
    return {
        "dm": dm,
        "owner": dm.owner,

        "cvp": dm.context["collateral_vault_peripheral"].contract,
        "cvc": dm.context["collateral_vault_core"].contract,
        "pvc": dm.context["cryptopunks_vault_core"].contract,
        "lpc": dm.context["lending_pool_core"].contract,
        "lpl": dm.context["lending_pool_lock"].contract,
        "lpp": dm.context["lending_pool_peripheral"].contract,
        "lp": dm.context["loans"].contract,
        "lc": dm.context["loans_core"].contract,
        "lic": dm.context["liquidations_core"].contract,
        "lip": dm.context["liquidations_peripheral"].contract,
        "ctrl": dm.context["liquidity_controls"].contract,

        "weth": dm.context["weth"].contract,

        "cool": dm.context["cool"].contract,
        "hm": dm.context["hm"].contract,
        "bakc": dm.context["bakc"].contract,
        "doodles": dm.context["doodles"].contract,
        "wow": dm.context["wow"].contract,
        "mayc": dm.context["mayc"].contract,
        "vft": dm.context["vft"].contract,
        "ppg": dm.context["ppg"].contract,
        "bayc": dm.context["bayc"].contract,
        "wpunk": dm.context["wpunk"].contract,
        "punk": dm.context["punk"].contract,
        "chromie": dm.context["chromie"].contract,
        "ringers": dm.context["ringers"].contract,
        "gazers": dm.context["gazers"].contract,
        "fidenza": dm.context["fidenza"].contract
    }

    # dm = DeploymentManager(ENV)
    # for k, v in dm.context.contract.items():
    #     globals()[k.replace(".", "_")] = v.contract
    #     print(k.replace(".", "_"),v.contract)
    # for k, v in dm.context.config.items():
    #     globals()[k.replace(".", "_")] = v
