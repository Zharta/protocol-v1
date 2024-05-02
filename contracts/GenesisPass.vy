# @version 0.3.10

## Interfaces

from vyper.interfaces import ERC165
from vyper.interfaces import ERC721

implements: ERC721
implements: ERC165

interface ERC721Receiver:
    def onERC721Received(_operator: address, _from: address, _tokenId: uint256, _data: Bytes[1024]) -> bytes4: view


## Events

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    tokenId: indexed(uint256)

event Approval:
    owner: indexed(address)
    approved: indexed(address)
    tokenId: indexed(uint256)

event ApprovalForAll:
    owner: indexed(address)
    operator: indexed(address)
    approved: bool

# EIP2309
event ConsecutiveTransfer:
    fromTokenId: indexed(uint256)
    toTokenId: uint256
    fromAddress: indexed(address)
    toAddress: indexed(address)

# Mimics OpenZeppelin's Ownable contract module
event OwnershipTransferred:
    previousOwner: indexed(address)
    newOwner: indexed(address)


# Global variables


# @dev Mapping from NFT ID to the address that owns it.
tokenOwner: HashMap[uint256, address]

# @dev Mapping from owner address to count of his tokens.
walletSupply: HashMap[address, uint256]

# @dev Mapping from NFT ID to the position in the wallet that owns it.
walletPosition: HashMap[uint256, uint256]

# @dev Mapping from owner address to NFTs
wallet: public(HashMap[address, DynArray[uint256, 2**32]])

# @dev Mapping from tokenId to approved address
tokenApprovals: HashMap[uint256, address]

# @dev Mapping from owner to operator approvals.
isApprovedForAll: public(HashMap[address, HashMap[address, bool]])

# @dev Address receiving the initially minted tokens
distributor: immutable(address)

owner: public(address)

totalSupply: public(constant(uint256)) = 65

BASE_URL: constant(String[30]) = "https://genesis.zharta.io/nft/"

contractURI: public(constant(String[34])) = "https://genesis.zharta.io/metadata"

SUPPORTED_INTERFACES: constant(bytes4[4]) = [
    0x01ffc9a7, # ERC165 interface ID of ERC165
    0x80ac58cd, # ERC165 interface ID of ERC721
    0x5b5e139f, # ERC165 interface ID of the ERC-721 metadata extension
    0x780E9D63, # ERC165 interface ID of the ERC-721 enumeration extension
]

name: public(immutable(String[19]))

symbol: public(immutable(String[3]))

## Constructor

@external
def __init__(_initialMintWallet: address):
    self.owner = msg.sender

    distributor = _initialMintWallet
    name = "Zharta Genesis Pass"
    symbol = "ZGP"

    for i in range(1, totalSupply+1):
        self.tokenOwner[i] = _initialMintWallet
        self._addTokenToEnumeration(_initialMintWallet, i)
    self.walletSupply[_initialMintWallet] = totalSupply

    log ConsecutiveTransfer(1, totalSupply, empty(address), _initialMintWallet)
    log OwnershipTransferred(empty(address), msg.sender)

## Internal View Functions

@view
@internal
def _isApprovedOrOwner(_wallet: address, _tokenId: uint256) -> bool:
    owner: address = self.tokenOwner[_tokenId]
    return _wallet == owner or _wallet == self.tokenApprovals[_tokenId] or self.isApprovedForAll[owner][_wallet]


## Internal Write Functions

@internal
def _addTokenToEnumeration(_to: address, _tokenId: uint256):
    """
    @dev Add a NFT to a given address enumeration
    """
    self.walletPosition[_tokenId] = len(self.wallet[_to])
    self.wallet[_to].append(_tokenId)



@internal
def _removeTokenFromEnumeration(_from: address, _tokenId: uint256):
    """
    @dev Remove a NFT from a given address enumeration
    """
    last: uint256 = self.wallet[_from].pop()
    if last != _tokenId:
        self.wallet[_from][self.walletPosition[_tokenId]] = last
        self.walletPosition[last] = self.walletPosition[_tokenId]
    self.walletPosition[_tokenId] = max_value(uint256)


@internal
def _transferFrom(_from: address, _to: address, _tokenId: uint256):
    """
    @dev Execute transfer of a NFT.
         Throws unless `msg.sender` is the current owner, an authorized operator, or the approved address for this NFT.
         Throws if `_to` is the zero address.
         Throws if `_from` is not the current owner.
         Throws if `_tokenId` is not a valid NFT.
    """

    assert _from != empty(address), "_from is zero addr"
    assert self._isApprovedOrOwner(msg.sender, _tokenId), "sender not owner nor approved"
    assert _from == self.tokenOwner[_tokenId], "_from is not owner"
    assert _to != empty(address), "_to is zero addr"

    self.tokenOwner[_tokenId] = _to
    self.tokenApprovals[_tokenId] = empty(address)

    self.walletSupply[_from] = unsafe_sub(self.walletSupply[_from], 1)
    self.walletSupply[_to] = unsafe_add(self.walletSupply[_to], 1)

    self._removeTokenFromEnumeration(_from, _tokenId)
    self._addTokenToEnumeration(_to, _tokenId)

    log Transfer(_from, _to, _tokenId)


## External View Functions

@pure
@external
def supportsInterface(interfaceID: bytes4) -> bool:

    """
    @notice Query if a contract implements an interface
    @param interfaceID The interface identifier, as specified in ERC-165
    @dev Interface identification is specified in ERC-165. This function uses less than 30,000 gas.
    @return `true` if the contract implements `interfaceID` and `interfaceID` is not 0xffffffff, `false` otherwise
    """

    return interfaceID in SUPPORTED_INTERFACES


@view
@external
def balanceOf(_owner: address) -> uint256:

    """
    @notice Count all NFTs assigned to an owner
    @dev NFTs assigned to the zero address are considered invalid, and this function throws for queries about the zero address.
    @param _owner An address for whom to query the balance
    @return The number of NFTs owned by `_owner`, possibly zero
    """

    assert _owner != empty(address), "owner is zero addr"
    return self.walletSupply[_owner]


@view
@external
def ownerOf(_tokenId: uint256) -> address:

    """
    @notice Find the owner of an NFT
    @dev NFTs assigned to zero address are considered invalid, and queries about them do throw.
    @param _tokenId The identifier for an NFT
    @return The address of the owner of the NFT
    """

    owner: address = self.tokenOwner[_tokenId]
    assert owner != empty(address), "owner is zero addr"
    return owner


@view
@external
def getApproved(_tokenId: uint256) -> address:

    """
    @notice Get the approved address for a single NFT
    @dev Throws if `_tokenId` is not a valid NFT.
    @param _tokenId The NFT to find the approved address for
    @return The approved address for this NFT, or the zero address if there is none
    """

    assert self.tokenOwner[_tokenId] != empty(address), "token not minted"
    return self.tokenApprovals[_tokenId]


@view
@external
def tokenURI(tokenId: uint256) -> String[110]:

    """
    @notice A distinct Uniform Resource Identifier (URI) for a given asset.
    @dev Throws if `_tokenId` is not a valid NFT. URIs are defined in RFC 3986.
     The URI may point to a JSON file that conforms to the "ERC721 Metadata JSON Schema".
    """

    return concat(BASE_URL, uint2str(tokenId))


@external
@view
def tokenByIndex(_index: uint256) -> uint256:

    """
    @notice Enumerate valid NFTs
    @dev Throws if `_index` >= `totalSupply()`.
    @param _index A counter less than `totalSupply()`
    @return The token identifier for the `_index`th NFT, (sort order not specified)
    """

    assert _index < totalSupply, "index out of bounds"
    return unsafe_add(_index, 1)


@external
@view
def tokenOfOwnerByIndex(_owner: address, _index: uint256) -> uint256:

    """
    @notice Enumerate NFTs assigned to an owner
    @dev Throws if `_index` >= `balanceOf(_owner)` or if `_owner` is the zero address, representing invalid NFTs.
    @param _owner An address where we are interested in NFTs owned by them
    @param _index A counter less than `balanceOf(_owner)`
    @return The token identifier for the `_index`th NFT assigned to `_owner`, (sort order not specified)
    """

    assert _index < self.walletSupply[_owner], "index out of bounds"
    return self.wallet[_owner][_index]


## External Write Functions

@external
def transferFrom(_from: address, _to: address, _tokenId: uint256):

    """
    @notice Transfer ownership of an NFT -- THE CALLER IS RESPONSIBLE TO CONFIRM THAT `_to` IS CAPABLE OF RECEIVING NFTS
     OR ELSE THEY MAY BE PERMANENTLY LOST
    @dev Throws unless `msg.sender` is the current owner, an authorized operator, or the approved address for this NFT.
     Throws if `_from` is not the current owner. Throws if `_to` is the zero address. Throws if `_tokenId` is not a valid NFT.
    @param _from The current owner of the NFT
    @param _to The new owner
    @param _tokenId The NFT to transfer
    """

    self._transferFrom(_from, _to, _tokenId)


@external
def safeTransferFrom(_from: address, _to: address, _tokenId: uint256, data: Bytes[1024]=b""):

    """
    @notice Transfers the ownership of an NFT from one address to another address
    @dev Throws unless `msg.sender` is the current owner, an authorized operator, or the approved address for this NFT. Throws if `_from` is
     not the current owner. Throws if `_to` is the zero address. Throws if `_tokenId` is not a valid NFT. When transfer is complete, this function
     checks if `_to` is a smart contract (code size > 0). If so, it calls `onERC721Received` on `_to` and throws if the return value is not
     `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`.
    @param _from The current owner of the NFT
    @param _to The new owner
    @param _tokenId The NFT to transfer
    @param data Optional additional data with no specified format, sent in call to `_to`
    """

    self._transferFrom(_from, _to, _tokenId)
    if _to.is_contract:
        returnValue: bytes4 = ERC721Receiver(_to).onERC721Received(msg.sender, _from, _tokenId, data)
        assert returnValue == method_id("onERC721Received(address,address,uint256,bytes)", output_type=bytes4), "transfer to non-ERC721Receiver"


@external
def approve(_approved: address, _tokenId: uint256):

    """
    @notice Change or reaffirm the approved address for an NFT
    @dev The zero address indicates there is no approved address.
     Throws unless `msg.sender` is the current NFT owner, or an authorized operator of the current owner.
    @param _approved The new approved NFT controller
    @param _tokenId The NFT to approve
    """

    _owner: address = self.tokenOwner[_tokenId]

    assert _approved != _owner, "approval to current owner"
    assert msg.sender == _owner or self.isApprovedForAll[_owner][msg.sender], "caller not owner nor operator"

    self.tokenApprovals[_tokenId] = _approved
    log Approval(_owner, _approved, _tokenId)


@external
def setApprovalForAll(_operator: address, _approved: bool):

    """
    @notice Enable or disable approval for a third party ("operator") to manage all of `msg.sender`'s assets
    @dev Emits the ApprovalForAll event. The contract MUST allow multiple operators per owner.
    @param _operator Address to add to the set of authorized operators
    @param _approved True if the operator is approved, false to revoke approval
    """

    assert msg.sender != _operator, "approve to sender"

    self.isApprovedForAll[msg.sender][_operator] = _approved
    log ApprovalForAll(msg.sender, _operator, _approved)


@external
def transferOwnership(_newOwner: address):

    """
    @notice Transfers ownership of the contract to a new account, can only be called by the current owner
    @dev Emits the OwnershipTransferred event
    @param _newOwner Address to transfer the ownership to
    """

    assert msg.sender == self.owner, "caller is not the owner"
    assert _newOwner != empty(address), "new owner is the zero address"

    log OwnershipTransferred(self.owner, _newOwner)
    self.owner = _newOwner


@external
def renounceOwnership():

    """
    @notice Leaves the contract without owner - not supported
    @dev Always throws, just here to be consistent with the OpenZeppelin Ownable module public functions
    """

    raise "not supported"
