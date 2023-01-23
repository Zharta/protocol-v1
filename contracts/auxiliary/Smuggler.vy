# @version 0.3.7

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
