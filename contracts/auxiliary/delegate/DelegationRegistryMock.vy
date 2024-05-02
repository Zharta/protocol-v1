# @version 0.3.10

# Structs

enum DelegationType:
    NULL
    ALL
    CONTRACT
    TOKEN

struct DelegationInfo:
    type: DelegationType
    vault: address
    delegate: address
    contract: address
    tokenId: uint256

struct ContractDelegation:
    contract: address
    delegate: address

struct TokenDelegation:
    contract: address
    tokenId: uint256
    delegate: address

# Events

event DelegateForAll:
    vault: address
    delegate: address
    value: bool

event DelegateForContract:
    vault: address
    delegate: address
    contract: address
    value: bool

event DelegateForToken:
    vault: address
    delegate: address
    contract: address
    tokenId: uint256
    value: bool

event RevokeAllDelegates:
    vault: address

event RevokeDelegate:
    vault: address
    delegate: address


# Global variables

delegations: HashMap[address, HashMap[uint256, DynArray[bytes32, 2**20]]]  #  vault -> vaultVersion -> delegationHash
vaultVersion: HashMap[address, uint256]
delegateVersion: HashMap[address, HashMap[address, uint256]]  # wallet -> delegate -> version
delegationHashes: HashMap[address, DynArray[bytes32, 2**20]]
delegationInfo: HashMap[bytes32, DelegationInfo]

delegationsIndex: HashMap[bytes32, uint256]
delegationHashesIndex: HashMap[bytes32, uint256]

# Internal functions

@view
@internal
def _computeAllDelegationHash(vault: address, delegate: address) -> bytes32:
    return keccak256(_abi_encode(
        delegate,
        vault,
        self.vaultVersion[vault],
        self.delegateVersion[vault][delegate]
    ))

@view
@internal
def _computeContractDelegationHash(vault: address, delegate: address, contract: address) -> bytes32:
    return keccak256(_abi_encode(
        delegate,
        vault,
        contract,
        self.vaultVersion[vault],
        self.delegateVersion[vault][delegate]
    ))

@view
@internal
def _computeTokenDelegationHash(vault: address, delegate: address, contract: address, tokenId: uint256) -> bytes32:
    return keccak256(_abi_encode(
        delegate,
        vault,
        contract,
        tokenId,
        self.vaultVersion[vault],
        self.delegateVersion[vault][delegate]
    ))


@internal
def _addDelegation(delegate: address, delegateHash: bytes32, type: DelegationType, vault: address, contract: address, tokenId: uint256):

    self.delegationsIndex[delegateHash] = len(self.delegations[vault][self.vaultVersion[vault]])
    self.delegations[vault][self.vaultVersion[vault]].append(delegateHash)
    self.delegationHashesIndex[delegateHash] = len(self.delegationHashes[delegate])
    self.delegationHashes[delegate].append(delegateHash)
    self.delegationInfo[delegateHash] = DelegationInfo({
        type: type,
        vault: vault,
        delegate: delegate,
        contract: contract,
        tokenId: tokenId
    })


@internal
def _removeDelegation(delegate: address, delegateHash: bytes32, vault: address):

    delegationsLast: bytes32 = self.delegations[vault][self.vaultVersion[vault]].pop()
    if delegationsLast != delegateHash:
        self.delegations[vault][self.vaultVersion[vault]][self.delegationsIndex[delegateHash]] = delegationsLast
        self.delegationsIndex[delegationsLast] = self.delegationsIndex[delegateHash]
    self.delegationsIndex[delegateHash] = max_value(uint256)

    delegationHashesLast: bytes32 = self.delegationHashes[delegate].pop()
    if delegationHashesLast != delegateHash:
        self.delegationHashes[delegate][self.delegationHashesIndex[delegateHash]] = delegationHashesLast
        self.delegationHashesIndex[delegationHashesLast] = self.delegationHashesIndex[delegateHash]
    self.delegationHashesIndex[delegateHash] = max_value(uint256)

    self.delegationInfo[delegateHash] = empty(DelegationInfo)


@internal
def _setDelegationValues(delegate: address, delegateHash: bytes32, _value: bool, type: DelegationType, vault: address, contract: address, tokenId: uint256):
    infoExists: bool = self.delegationInfo[delegateHash].vault != empty(address)
    if _value and not infoExists:
        self._addDelegation(delegate, delegateHash, type, vault, contract, tokenId)
    elif not _value and infoExists:
        self._removeDelegation(delegate, delegateHash, vault)


@internal
def _revokeDelegate(delegate: address, vault: address):
    self.delegateVersion[vault][delegate] += 1
    log RevokeDelegate(vault, msg.sender)

@view
@internal
def _checkDelegationExistsForVault(vault: address, delegateHash: bytes32) -> bool:
    return self.delegationInfo[delegateHash].vault != empty(address) and \
        self.delegationsIndex[delegateHash] < len(self.delegations[vault][self.vaultVersion[vault]])


@view
@internal
def _checkDelegateForAll(delegate: address, vault: address) -> bool:
    return self._checkDelegationExistsForVault(vault, self._computeAllDelegationHash(vault, delegate))


@view
@internal
def _checkDelegateForContract(delegate: address , vault: address , contract: address ) -> bool:
    delegateHash: bytes32 = self._computeContractDelegationHash(vault, delegate, contract)
    return self._checkDelegationExistsForVault(vault, delegateHash) or self._checkDelegateForAll(delegate, vault)


@view
@internal
def _checkDelegateForToken(delegate: address, vault: address , contract: address , tokenId: uint256) -> bool:
    delegateHash: bytes32 = self._computeTokenDelegationHash(vault, delegate, contract, tokenId)
    return self._checkDelegationExistsForVault(vault, delegateHash) or self._checkDelegateForContract(delegate, vault, contract)


@view
@internal
def _getDelegatesForLevel(vault: address , delegationType: DelegationType, contract: address , tokenId: uint256) -> DynArray[address, 2**10]:
    delegatesForLevel: DynArray[address, 2**10] = []
    _len: uint256 = len(self.delegations[vault][self.vaultVersion[vault]])
    for i in range(2**10):
        if i < _len:
            delegationHash: bytes32 = self.delegations[vault][self.vaultVersion[vault]][i]
            delegationInfo: DelegationInfo = self.delegationInfo[delegationHash]
            if delegationType == DelegationType.ALL and delegationHash == self._computeAllDelegationHash(vault, delegationInfo.delegate):
                delegatesForLevel.append(delegationInfo.delegate)
            elif delegationType == DelegationType.CONTRACT and delegationHash == self._computeContractDelegationHash(vault, delegationInfo.delegate, contract):
                delegatesForLevel.append(delegationInfo.delegate)
            elif delegationType == DelegationType.TOKEN and delegationHash == self._computeTokenDelegationHash(vault, delegationInfo.delegate, contract, tokenId):
                delegatesForLevel.append(delegationInfo.delegate)
    return delegatesForLevel



# External read functions

@view
@external
def getDelegatesForAll(vault: address) -> DynArray[address, 2**10]:
    return self._getDelegatesForLevel(vault, DelegationType.ALL, empty(address), 0)


@view
@external
def getDelegatesForContract(vault: address, contract: address) -> DynArray[address, 2**10]:
    return self._getDelegatesForLevel(vault, DelegationType.CONTRACT, contract, 0)


@view
@external
def getDelegatesForToken(vault: address, contract: address, tokenId: uint256) -> DynArray[address, 2**10]:
    return self._getDelegatesForLevel(vault, DelegationType.TOKEN, contract, tokenId)


@view
@external
def getContractLevelDelegations(vault: address) -> DynArray[ContractDelegation, 2**10]:
    return [] # not implemented


@view
@external
def getTokenLevelDelegations(vault: address) -> DynArray[TokenDelegation, 2**10]:
    return [] # not implemented


@view
@external
def checkDelegateForAll(delegate: address, vault: address) -> bool:
    return self._checkDelegateForAll(delegate, vault)


@view
@external
def checkDelegateForContract(delegate: address , vault: address , contract: address ) -> bool:
    return self._checkDelegateForContract(delegate, vault, contract)


@view
@external
def checkDelegateForToken(delegate: address, vault: address , contract: address , tokenId: uint256) -> bool:
    return self._checkDelegateForToken(delegate, vault, contract, tokenId)


@view
@external
def getDelegationsByDelegate(delegate: address) -> DynArray[DelegationInfo, 2**10]:
    _delegations: DynArray[DelegationInfo, 2**10] = []
    _len: uint256 = len(self.delegationHashes[delegate])
    for i in range(2**10):
        if i < _len:
            delegationHash: bytes32 = self.delegationHashes[delegate][i]
            delegationInfo: DelegationInfo = self.delegationInfo[delegationHash]
            computedHash: bytes32 = empty(bytes32)
            if delegationInfo.type == DelegationType.ALL:
                computedHash = self._computeAllDelegationHash(delegationInfo.vault, delegate)
            elif delegationInfo.type == DelegationType.CONTRACT:
                computedHash = self._computeContractDelegationHash(delegationInfo.vault, delegate, delegationInfo.contract)
            elif delegationInfo.type == DelegationType.TOKEN:
                computedHash = self._computeTokenDelegationHash(delegationInfo.vault, delegate, delegationInfo.contract, delegationInfo.tokenId)

            if delegationHash == computedHash:
                _delegations.append(delegationInfo)
    return _delegations



# External write functions

@external
def __init__():
    pass


@external
def delegateForAll(delegate: address, _value: bool):
    delegationHash: bytes32 = self._computeAllDelegationHash(msg.sender, delegate)
    self._setDelegationValues(delegate, delegationHash, _value, DelegationType.ALL, msg.sender, empty(address), 0)
    log DelegateForAll(msg.sender, delegate, _value)


@external
def delegateForContract(delegate: address, contract: address, _value: bool):
    delegationHash: bytes32 = self._computeContractDelegationHash(msg.sender, delegate, contract)
    self._setDelegationValues(delegate, delegationHash, _value, DelegationType.CONTRACT, msg.sender, contract, 0)
    log DelegateForContract(msg.sender, delegate, contract, _value)


@external
def delegateForToken(delegate: address, contract: address, tokenId: uint256, _value: bool):
    delegationHash: bytes32 = self._computeTokenDelegationHash(msg.sender, delegate, contract, tokenId)
    self._setDelegationValues(delegate, delegationHash, _value, DelegationType.TOKEN, msg.sender, contract, tokenId)
    log DelegateForToken(msg.sender, delegate, contract, tokenId, _value)


@external
def revokeAllDelegates():
    self.vaultVersion[msg.sender] += 1
    log RevokeAllDelegates(msg.sender)


@external
def revokeDelegate(delegate: address):
    self._revokeDelegate(delegate, msg.sender)


@external
def revokeSelf(vault: address):
    self._revokeDelegate(msg.sender, vault)
