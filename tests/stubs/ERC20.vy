# Structs

# Events

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

# Functions

@view
@external
def name() -> String[32]:
    return ""

@view
@external
def symbol() -> String[32]:
    return ""

@view
@external
def decimals() -> uint8:
    return 0

@view
@external
def balanceOf(arg0: address) -> uint256:
    return 0

@view
@external
def allowance(arg0: address, arg1: address) -> uint256:
    return 0

@view
@external
def totalSupply() -> uint256:
    return 0

@external
def transfer(_to: address, _value: uint256) -> bool:
    return False

@external
def transferFrom(_from: address, _to: address, _value: uint256) -> bool:
    return False

@external
def approve(_spender: address, _value: uint256) -> bool:
    return False

@external
def mint(_to: address, _value: uint256):
    pass

@external
def burn(_value: uint256):
    pass

@external
def burnFrom(_to: address, _value: uint256):
    pass
