from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import (
    MPTAmount,
    MPTokenIssuanceCreate,
    MPTokenIssuanceSet,
    MPTokenIssuanceSetFlag,
    AccountObjectType,
    MPTokenIssuanceDestroy,
    Clawback,
    MPTokenIssuanceCreateFlag,
    Payment,
    AccountObjects,
    LedgerEntry,
    AccountObjectType,
    MPTokenAuthorizeFlag,
    MPTokenAuthorize,
)
from xrpl.transaction import submit_and_wait, sign_and_submit
from misc import (
    hex_to_symbol,
    mm,
    nft_fee_to_xrp_format,
    symbol_to_hex,
    transfer_fee_to_xrp_format,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    xrp_format_to_nft_fee,
)
from xrpl.utils import ripple_time_to_datetime, str_to_hex
from x_constants import M_SOURCE_TAG, MPTOKEN_FLAGS, MPTOKEN_ISSUANCE_FLAGS, XURLS_


# https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens

# region POST


#
def create_mpt_token(
    sender_addr: str,
    total_supply: str,
    scale: int = None,
    can_transfer: bool = False,
    can_clawback: bool = False,
    can_escrow: bool = False,
    can_trade: bool = False,
    can_lock: bool = False,
    require_auth: bool = False,
    transfer_fee: float = None,
    metadata: str = None,
    fee: str = None,
):
    flags = []
    if can_transfer:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRANSFER)
    if can_clawback:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_CAN_CLAWBACK)
    if can_escrow:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_CAN_ESCROW)
    if can_trade:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_CAN_TRADE)
    if can_lock:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_CAN_LOCK)
    if require_auth:
        flags.append(MPTokenIssuanceCreateFlag.TF_MPT_REQUIRE_AUTH)

    txn = MPTokenIssuanceCreate(
        account=sender_addr,
        mptoken_metadata=str_to_hex(metadata),
        maximum_amount=total_supply,
        transfer_fee=nft_fee_to_xrp_format(transfer_fee) if transfer_fee != None else 0,
        asset_scale=scale,
        flags=flags,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )

    return txn.to_xrpl()


# to be called by the issuer
def mpt_authorize(
    sender_addr: str,
    mpt_issuance_id: str,
    target_addr: str,
    fee: str = None,
):
    """authorize an account to transact with your mpt"""
    txn = MPTokenAuthorize(
        account=sender_addr,
        mptoken_issuance_id=mpt_issuance_id,
        holder=target_addr,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )
    return txn.to_xrpl()


# to be called by receiver
def mpt_optin():
    pass


def mpt_optout():
    pass


# mpt lock and global lock
# mpt unlock and global unlock

# mpt authorize and global
# mpt unauthorize and global


def mpt_clawback(
    sender_addr: str,
    mpt_issuance_id: str,
    amount: str,
    target_addr: str,
    fee: str = None,
):
    "clawback an mpt from an target addr"
    txn = Clawback(
        account=sender_addr,
        amount=MPTAmount(
            mpt_issuance_id=mpt_issuance_id,
            value=amount,
        ),
        holder=target_addr,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )
    return txn.to_xrpl()


def delete_mpt(
    sender_addr: str,
    mpt_issuance_id: str,
    fee: str = None,
) -> dict:
    "destroy the mpt"
    # https://xrpl.org/docs/references/protocol/transactions/types/mptokenissuancedestroy
    txn = MPTokenIssuanceDestroy(
        account=sender_addr,
        mptoken_issuance_id=mpt_issuance_id,
        fee=fee,
        source_tag=M_SOURCE_TAG,
        memos=mm(),
    )
    return txn.to_xrpl()


# endregion


# region GET


def parse_created_mpt_flags(mpt_issuance_flag: int) -> list:
    flags = []
    for flag in MPTOKEN_ISSUANCE_FLAGS:
        if flag["hex"] & mpt_issuance_flag == flag["hex"]:
            flags.append(flag)
    return flags


def parse_mpt_flags(mpt_flag: int) -> list:
    flags = []
    for flag in MPTOKEN_FLAGS:
        if flag["hex"] & mpt_flag == flag["hex"]:
            flags.append(flag)
    return flags


async def created_mpts(url: str, wallet_addr: str) -> list:
    """returns a list of the mpts an account has created"""
    mpts_ = []
    query = AccountObjects(
        account=wallet_addr,
        ledger_index="validated",
        type=AccountObjectType.MPT_ISSUANCE,
    )
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "account_objects" in result:
        account_mpts: list[dict] = result["account_objects"]
        for mpt in account_mpts:
            mpt_data = {}
            mpt_data["index"] = mpt["index"]
            mpt_data["mpt_issuance_id"] = mpt["mpt_issuance_id"]
            mpt_data["issuer"] = mpt["Issuer"]
            mpt_data["total_supply"] = (
                mpt["MaximumAmount"] if "MaximumAmount" in mpt else 0
            )
            mpt_data["circulating_supply"] = (
                mpt["OutstandingAmount"] if "OutstandingAmount" in mpt else 0
            )
            mpt_data["scale"] = mpt["AssetScale"] if "AssetScale" in mpt else 0
            mpt_data["transfer_fee"] = (
                xrp_format_to_nft_fee(mpt["TransferFee"]) if "TransferFee" in mpt else 0
            )

            mpt_data["flags"] = (
                parse_created_mpt_flags(mpt["Flags"]) if "Flags" in mpt else []
            )
            mpt_data["metadata"] = (
                mpt["MPTokenMetadata"] if "MPTokenMetadata" in mpt else ""
            )
            mpts_.append(mpt_data)
    return mpts_


async def account_mpts(url: str, wallet_addr: str) -> list:
    "mpts in account balance"
    mpts_ = []
    query = AccountObjects(
        account=wallet_addr,
        ledger_index="validated",
        type=AccountObjectType.MPTOKEN,
    )
    response = await AsyncJsonRpcClient(url).request(query)
    result = response.result
    if "account_objects" in result:
        owned_mpts: list[dict] = result["account_objects"]
        for mpt in owned_mpts:
            mpt_data = {}
            mpt_data["index"] = mpt["index"]
            mpt_data["mpt_issuance_id"] = mpt["MPTokenIssuanceID"]
            mpt_data["balance"] = mpt["MPTAmount"] if "MPTAmount" in mpt else 0
            mpt_data["flags"] = parse_mpt_flags(mpt["Flags"]) if "Flags" in mpt else []
            mpts_.append(mpt_data)
    return mpts_

    pass


# appears uneccessary
async def mpt_info():
    pass


# endregion

import asyncio


print(
    asyncio.run(
        account_mpts(
            "https://s.devnet.rippletest.net:51234/",
            "rPw2ZCUqCqzHZbXa5nFnPmG48HMZc2rrV3",
            # ""
        )
    )
)
