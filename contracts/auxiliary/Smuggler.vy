# @version 0.4.0

"""
Test contract to deliver funds to non payable contracts
"""


@external
@payable
def __default__():
    pass



@external
def deliver(_to: address):
    selfdestruct(_to)
