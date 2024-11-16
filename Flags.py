from xrpl.models import AccountSet, AccountSetAsfFlag
from Misc import mm
from x_constants import M_SOURCE_TAG

# Read More
# https://xrpl.org/accountset.html#accountset-flags


# Account Set Flags - asf
"""
To enable the asfDisableMaster or asfNoFreeze flags,
you must authorize the transaction by signing it with the master key pair.
You cannot use a regular key pair or a multi-signature.
You can disable asfDisableMaster (that is, re-enable the master key pair) using a regular key pair or multi-signature.

"""

# Account Txn Id - reversible ?
def account_txn_id(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_ACCOUNT_TXN_ID, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_ACCOUNT_TXN_ID, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Default Ripple - reversible ?
# Enable rippling by default on the accounts trustlines
def default_ripple(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Deposit Authorization - reversible
# https://xrpl.org/depositauth.html
def deposit_authorization(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Disable Master Key - reversible ?
def disable_master_key(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Disallow XRP - reversible (should be enforced by client)
def disallow_XRP(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISALLOW_XRP, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DISALLOW_XRP, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Global Freeze - reversible if no freeze is disabled
# Freeze all tokens issued by this account
def global_freeze(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_GLOBAL_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_GLOBAL_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# No Freeze, ever | Freeze no more - irreversible
def no_freeze(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_NO_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_NO_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()    

# Require Authorization - reversible ? 
# Other accounts require authorization to hold tokens issued by my account
def require_authorization(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Require Destination Tag - reversible ? 
# Other accounts should use a destination tag when sending transactions to my account
def require_destination_tag(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_REQUIRE_DEST, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_REQUIRE_DEST, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Designate NFT Minter - research about reversing
# Allow another account to mint and burn tokens on behalf of my account.
def designate_NFT_minter(sender_addr: str, minter: str = None, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_AUTHORIZED_NFTOKEN_MINTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_AUTHORIZED_NFTOKEN_MINTER, fee=fee, nftoken_minter=minter, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Block NFT Offers - reversible
# No account should to create nft offers directed at my account
def block_NFT_offers(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_NFTOKEN_OFFER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_NFTOKEN_OFFER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Block Incoming Checks - reversible
# No account should to create checks directed at my account
def block_incoming_checks(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_CHECK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_CHECK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Block Incoming Payment Channels - reversible
# No account should to create payment channels directed at my account
def block_incoming_payment_channels(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_PAYCHAN, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_PAYCHAN, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()


# Block Incoming Trustlines - reversible
# No account should to create trustlines directed at my account
def block_incoming_trustlines(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_TRUSTLINE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_TRUSTLINE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# Enable Clawback - irreversible
# Allow my account to retrieve its issued tokens from another account
def enable_clawback(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()