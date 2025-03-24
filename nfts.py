from xrpl.models import (
    NFTokenMint,
    NFTokenBurn,
    NFTokenMintFlag,
    AccountNFTs,
    NFTokenAcceptOffer,
    NFTokenCreateOffer,
    NFTokenCreateOfferFlag,
    Memo,
)
from xrpl.utils import (
    drops_to_xrp,
    ripple_time_to_datetime,
    xrp_to_drops,
    datetime_to_ripple_time,
)
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.transaction.main import sign_and_submit
import requests

from misc import (
    memo_builder,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    mm,
    nft_fee_to_xrp_format,
    xrp_format_to_nft_fee,
)
from x_constants import M_SOURCE_TAG, NFTOKEN_FLAGS
from xrpl.wallet import Wallet

# https://xrpl.org/docs/concepts/tokens/nfts
# https://xrpl.org/docs/references/protocol/data-types/nftoken

# region POST


def issue_nft(
    sender_addr: str,
    taxon: int,
    is_transferable: bool,
    only_xrp: bool,
    issuer_burn: bool,
    issuer_addr: str = None,
    transfer_fee: float = None,
    uri: str = None,
    fee: str = None,
) -> dict:
    flag = []
    if is_transferable:
        flag.append(NFTokenMintFlag.TF_TRANSFERABLE)  # nft can be transferred
    if only_xrp:
        flag.append(NFTokenMintFlag.TF_ONLY_XRP)  # nft may be traded for xrp only
    if issuer_burn:
        flag.append(
            NFTokenMintFlag.TF_BURNABLE
        )  # If set, indicates that the minted token may be burned by the issuer even if the issuer does not currently hold the token.

    txn = NFTokenMint(
        account=sender_addr,
        issuer=issuer_addr,  # Indicates the account that should be the issuer of this token, is nullable.
        # If provided, the issuer's AccountRoot object must have the NFTokenMinter field set to the sender of this transaction (this transaction's Account field).
        nftoken_taxon=taxon,
        uri=validate_symbol_to_hex(uri),
        flags=flag,
        transfer_fee=nft_fee_to_xrp_format(transfer_fee),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def burn_nft(
    sender_addr: str, nftoken_id: str, holder: str = None, fee: str = None
) -> dict:
    """burn an nft. Specify the holder if the token is not in your wallet, only issuer and holder can call"""
    txn = NFTokenBurn(
        account=sender_addr,
        nftoken_id=nftoken_id,
        owner=holder,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# endregion


# region GET


def parse_nft_flags(nft_flag: int) -> list:
    flags = []
    for flag in NFTOKEN_FLAGS:
        if flag["hex"] & nft_flag == flag["hex"]:
            flags.append(flag)
    return flags


async def account_nfts(url: str, wallet_addr: str) -> list:
    "return all nfts an account is holding"
    account_nft = []
    req = AccountNFTs(account=wallet_addr, id="validated")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_nfts" in result:
        account_nfts = result["account_nfts"]
        for nfts in account_nfts:
            nft = {}
            nft["issuer"] = nfts["Issuer"]
            nft["nft_id"] = nfts["NFTokenID"]
            nft["taxon"] = nfts["NFTokenTaxon"]
            nft["serial"] = nfts["nft_serial"]
            nft["uri"] = validate_hex_to_symbol(nfts["URI"]) if "URI" in nfts else ""
            nft["transfer_fee"] = (
                xrp_format_to_nft_fee(nfts["TransferFee"])
                if "TransferFee" in nfts
                else 0
            )
            nft["flags"] = parse_nft_flags(nfts["Flags"]) if "Flags" in nfts else 0
            account_nft.append(nft)
    return account_nft


# external
async def nft_info(nft_id: str, mainnet: bool = True):
    """return information about a particular NFT\n this method uses an external api"""
    nft_info = {}
    response = (
        requests.get(f"https://api.xrpldata.com/api/v1/xls20-nfts/nft/{nft_id}").json()
        if mainnet
        else requests.get(
            f"https://test-api.xrpldata.com/api/v1/xls20-nfts/nft/{nft_id}"
        ).json()
    )
    if "data" in response and isinstance(response["data"]["nft"], dict):
        nft = response["data"]["nft"]
        nft_info["issuer"] = nft["Issuer"]
        nft_info["owner"] = nft["Owner"]
        nft_info["taxon"] = nft["Taxon"]
        nft_info["sequence"] = nft["Sequence"]
        nft_info["transfer_fee"] = xrp_format_to_nft_fee(nft["TransferFee"])
        nft_info["uri"] = validate_hex_to_symbol(nft["URI"])
        # nft_info["flags"] = nft["Flags"]  # parse flags
        nft_info["flags"] = parse_nft_flags(nft["Flags"])  # parse flags
    return nft_info


# external
async def created_nfts(wallet_addr: str, mainnet: bool = True) -> list:
    """return all nfts an account created as an issuer \n this method uses an external api"""
    created_nfts = []
    result = (
        requests.get(f"https://api.xrpldata.com/api/v1/xls20-nfts/issuer/{wallet_addr}")
        if mainnet
        else requests.get(
            f"https://test-api.xrpldata.com/api/v1/xls20-nfts/issuer/{wallet_addr}"
        )
    )
    result = result.json()
    if "data" in result and "nfts" in result["data"]:
        nfts = result["data"]["nfts"]
        for nft in nfts:
            nft_data = {}
            nft_data["nft_id"] = nft["NFTokenID"]
            nft_data["issuer"] = nft["Issuer"]
            nft_data["owner"] = nft["Owner"]
            nft_data["taxon"] = nft["Taxon"]
            nft_data["sequence"] = nft["Sequence"]
            nft_data["transfer_fee"] = xrp_format_to_nft_fee(nft["TransferFee"])
            nft_data["flags"] = parse_nft_flags(nft["Flags"])
            nft_data["uri"] = validate_hex_to_symbol(nft["URI"])
            created_nfts.append(nft_data)
    return created_nfts


# endregion


# from xrpl.models.transactions import Transaction
# from xrpl.clients import JsonRpcClient

# nft = issue_nft(
#     "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n",
# 100, True, False, True, None, 0.001, "nft.com",
# )


# issuer1 = Wallet.from_seed(
#     seed="sEdS1jTVU58HsPeL4xhPkziphnxFDHz"
# )

# client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
# # print(nft)


# print(sign_and_submit(Transaction.from_xrpl(nft), client, issuer1,).result )


# print(asyncio.run( account_nfts("https://s.altnet.rippletest.net:51234", "rpmsgLmYHky4Qw7fGu4jLr4Xu1dS5Q849n") ) )


# client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
# # client = JsonRpcClient("https://xrplcluster.com")
# info =  NFTInfo(
#     nft_id="00090001134CA9F08886BFDC5F0E996ADDB95DE9937EDFC3565BFADA00325E23"
# )
# res = client.request(info)
# print(res.result)
