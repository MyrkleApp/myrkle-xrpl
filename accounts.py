import asyncio
from misc import transfer_fee_to_xrp_format, validate_hex_to_symbol, xrp_format_to_transfer_fee
from xrpl.utils import (
    drops_to_xrp,
    ripple_time_to_datetime,
    xrp_to_drops,
    datetime_to_ripple_time,
    str_to_hex
)
from xrpl.models import (AccountSet, AccountSetAsfFlag, AccountDelete, DepositAuthorized, DepositPreauth, SetRegularKey, AccountInfo)


from misc import validate_hex_to_symbol, validate_symbol_to_hex, mm
from x_constants import ACCOUNT_ROOT_FLAGS, M_SOURCE_TAG, OFFER_FLAGS
from xrpl.asyncio.clients import AsyncJsonRpcClient


# TODO: signer list https://xrpl.org/docs/concepts/accounts/multi-signing

# black hole account

# every account level transaction

# https://xrpl.org/docs/references/protocol/transactions/types/accountset#accountset-flags
# https://xrpl.org/docs/references/protocol/transactions/types/accountset#nftokenminter
# https://xrpl.org/docs/references/protocol/transactions/types/setregularkey#setregularkey
# https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/accountroot


# region POST

"""start Flags"""

def default_ripple(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Enable rippling on this account's trust lines by default. Required for issuing addresses; discouraged for others."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DEFAULT_RIPPLE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def deposit_authorization(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """This account can only receive payments from transactions it initiates, and from [preauthorized accounts](link to deposit preauth)."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def disable_master_key(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Disallow the use of the master key to sign transactions for this account. Can only be enabled if the account has configured another way to sign transactions, such as a Regular Key or a Signer List."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DISABLE_MASTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def block_incoming_checks(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """No account should create checks directed to this account."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_CHECK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_CHECK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def block_incoming_nft_offers(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """No account should create nft offers directed to this account."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_NFTOKEN_OFFER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_NFTOKEN_OFFER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def block_incoming_payment_channels(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """No account should create payment channels directed to this account."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_PAYCHAN, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_PAYCHAN, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def block_incoming_trustlines(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """No account should create trustlines directed to this account."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_TRUSTLINE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_DISABLE_INCOMING_TRUSTLINE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def block_xrp(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """No account should send XRP to this account. Not enforced by the blockchain."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_DISALLOW_XRP, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_DISALLOW_XRP, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def global_freeze(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Freeze all assets issued by this account"""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_GLOBAL_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_GLOBAL_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def no_freeze(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Permanently give up the ability to freeze individual trust lines or modify Global Freeze. This flag can never be disabled after being enabled."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_NO_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_NO_FREEZE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()   


def require_authorization(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """This account must individually approve any account that wants to hold tokens it issues. Can only be enabled if this account has no trust lines connected to it."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_REQUIRE_AUTH, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def require_destination_tag(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Requires incoming payments to this account to specify a Destination Tag."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_REQUIRE_DEST, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_REQUIRE_DEST, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()


def trustline_clawback(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """This account can claw back tokens it has issued. Can only be set if the account has an empty owner directory (no trust lines, offers, escrows, payment channels, checks, or signer lists, etc). Once enabled it cannot be disabled."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_ALLOW_TRUSTLINE_CLAWBACK, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def authorize_nft_minter(sender_addr: str, minter: str = None, state: bool = False, fee: str = None) -> dict:
    """Allow another account to mint non-fungible tokens (NFTokens) on this account's behalf."""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_AUTHORIZED_NFTOKEN_MINTER, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr, set_flag=AccountSetAsfFlag.ASF_AUTHORIZED_NFTOKEN_MINTER, fee=fee, nftoken_minter=minter, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def account_transaction_id(sender_addr: str, state: bool = False, fee: str = None) -> dict:
    """Track the ID of this account's most recent transaction. Required for AccountTxnID"""
    txn = AccountSet(account=sender_addr, clear_flag=AccountSetAsfFlag.ASF_ACCOUNT_TXN_ID, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    if state:
        txn = AccountSet(account=sender_addr,  set_flag=AccountSetAsfFlag.ASF_ACCOUNT_TXN_ID, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

"""end Flags"""


"""start Fields"""
def modify_domain(sender_addr: str, domain: str, fee: str = None) -> dict:
    """modify the domain of this account"""
    txn = AccountSet(
        account=sender_addr,
        domain=validate_symbol_to_hex(domain),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_transfer_fee(sender_addr: str, transfer_fee: float, fee: str = None):
    """modify the transfer fee of tokens issued by this account"""
    txn = AccountSet(
        account=sender_addr,
        transfer_rate=transfer_fee_to_xrp_format(transfer_fee),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_ticksize(sender_addr: str, tick_size: int, fee: str = None):
    """modify the ticksize of this account"""
    txn = AccountSet(
        account=sender_addr,
        tick_size=tick_size,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_email(sender_addr: str, email: str, fee: str = None) -> dict:
    """modify the email of this"""
    txn = AccountSet(
        account=sender_addr,
        email_hash=str_to_hex(email),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_message_key(sender_addr: str, message_key: str, fee: str = None) -> dict:
    """modify the message key of this account"""
    txn = AccountSet(
        account=sender_addr,
        message_key=message_key,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()

"""end Fields"""

def delete_account(sender_addr: str, receiver_addr: str, receiver_destination_tag: str = None, fee: str = None) -> dict:
    """delete accounts on the ledger \n
    account must not own any ledger object, costs 2 xrp_chain fee, acc_seq + 256 > current_ledger_seq \n
    account can still be created after merge"""
    txn = AccountDelete(
        account=sender_addr,
        destination=receiver_addr,
        destination_tag=receiver_destination_tag,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()

def deposit_pre_authorization(sender_addr: str, authorize: str = None, unauthorize: str = None, fee: str = None) -> dict:
    """authorize or unauthorize an account to send you payments, if the deposut auth flag is enabled"""
    txn = DepositPreauth(account=sender_addr, authorize=authorize, unauthorize=unauthorize, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()


def modify_regular_key(sender_addr: str, regular_key_addr: str = None, fee: str = None) -> dict:
    """modify the regular key of an account. leave regular_key_addr empty to clear"""
    txn = SetRegularKey(account=sender_addr, regular_key=regular_key_addr, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()

def blackhole_account():
    """Although i am not sure, i am convinced blackholing an account, involves setting the rrr.. address
    as a regular key and then disabling the master key
    """
    pass


# endregion









# region GET
# for getting account information
def parse_account_flags(account_flag: int) -> list:
    """returns all the flags associated with an account"""
    flags = []
    for flag in ACCOUNT_ROOT_FLAGS:
        if flag["hex"] & account_flag == flag["hex"]:
            flags.append(flag)
    return flags

async def get_account_info(url: str, wallet_addr: str) -> dict:
    """returns information about an account"""
    account_info = {}
    query = AccountInfo(account=wallet_addr, ledger_index="validated")
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "account_data" in result:
        account_data = result["account_data"]
        account_info["index"] = account_data["index"]
        account_info["address"] = account_data["Account"]
        account_info["balance"] = str(drops_to_xrp(account_data["Balance"]))
        account_info["object_type"] = account_data["LedgerEntryType"]
        account_info["account_objects"] = account_data["OwnerCount"]
        account_info["sequence"] = account_data["Sequence"]
        account_info["tick_size"] = 0
        account_info["transfer_rate"] = 0.0
        account_info["domain"] = ""
        account_info["email"] = ""
        account_info["message_key"] = ""
        
        # call the xWallet.account_flags to populate this page
        if "TickSize" in account_data:
            account_info["tick_size"] = account_data["TickSize"]
        if "TransferRate" in account_data:
            account_info["transfer_rate"] = xrp_format_to_transfer_fee(
                account_data["TransferRate"]
            )
        if "Domain" in account_data:
            account_info["domain"] = validate_hex_to_symbol(account_data["Domain"])
        if "EmailHash" in account_data:
            account_info["email"] = validate_hex_to_symbol(
                account_data["EmailHash"]
            )
        if "MessageKey" in account_data:
            account_info["message_key"] = validate_hex_to_symbol(
                account_data["MessageKey"]
            )
        account_info["flags"] = parse_account_flags(account_data["Flags"])
    return account_info


async def is_deposit_authorized(url: str, sender_addr: str, receiver_addr: str) -> bool:
    """check if an account is authorized to send payments to another account"""
    value = False
    req = DepositAuthorized(source_account=sender_addr, destination_account=receiver_addr)
    response =  await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "deposit_authorized" in result:
        value = result["is_deposit_authorized"]
    return value

# endregion



# print(asyncio.run(get_account_info("https://s.altnet.rippletest.net:51234", "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n")))