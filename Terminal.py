from typing import Union
import requests
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import (
    AccountDelete,
    AccountInfo,
    AccountSet,
    GatewayBalances,
    IssuedCurrencyAmount,
    TrustSet,
    TrustSetFlag,
)
from Misc import (
    mm,
    transfer_fee_to_xrp_format,
    validate_hex_to_symbol,
    validate_symbol_to_hex,
    xrp_format_to_nft_fee,
)
from xrpl.utils import str_to_hex
from x_constants import M_SOURCE_TAG


class xEng(AsyncJsonRpcClient):
    def __init__(self, url: str) -> None:
        self.client = AsyncJsonRpcClient(url)


    # using gateway balance is compulsory, no choice - although some node may not accept the request
    async def created_tokens_issuer(self, wallet_addr: str) -> list:
        """returns all tokens an account has created as the issuer"""
        created_assets = []
        req = GatewayBalances(account=wallet_addr, ledger_index="validated")
        response = await self.client.request(req)
        result = response.result
        if "obligations" in result:
            obligations = result["obligations"]
            for key, value in obligations.items():
                asset = {}
                asset["token"] = validate_hex_to_symbol(key)
                asset["amount"] = value
                asset["issuer"] = wallet_addr
                asset["domain"] = ""
                acc_info = AccountInfo(account=wallet_addr, ledger_index="validated")
                account_data = await self.client.request(acc_info)
                account_data = account_data.result["account_data"]
                if "Domain" in account_data:
                    asset["domain"] = validate_hex_to_symbol(account_data["Domain"])
                created_assets.append(asset)
        return created_assets

    async def created_tokens_manager(self, wallet_addr: str) -> list:
        """returns all tokens an account thas created as the manager"""
        created_assets = []
        req = GatewayBalances(account=wallet_addr, ledger_index="validated")
        response = await self.client.request(req)
        result = response.result
        if "assets" in result:
            assets = result["assets"]
            for issuer, issuings in assets.items():
                for iss_cur in issuings:
                    asset = {}
                    asset["issuer"] = issuer
                    asset["token"] = validate_hex_to_symbol(iss_cur["currency"])
                    asset["amount"] = iss_cur["value"]
                    asset["manager"] = wallet_addr
                    asset["domain"] = ""
                    acc_info = AccountInfo(
                        account=asset["cold_address"], ledger_index="validated"
                    )
                    account_data = await self.client.request(acc_info)
                    account_data = account_data.result["account_data"]
                    if "Domain" in account_data:
                        asset["domain"] = validate_hex_to_symbol(account_data["Domain"])
                    created_assets.append(asset)
        return created_assets

    async def created_nfts(self, wallet_addr: str, mainnet: bool = True) -> list:
        """return all nfts an account created as an issuer \n this method uses an external api"""
        created_nfts = []
        result = (
            requests.get(
                f"https://api.xrpldata.com/api/v1/xls20-nfts/issuer/{wallet_addr}"
            )
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
                nft_data["nftoken_id"] = nft["NFTokenID"]
                nft_data["issuer"] = nft["Issuer"]
                nft_data["owner"] = nft["Owner"]
                nft_data["taxon"] = nft["Taxon"]
                nft_data["sequence"] = nft["Sequence"]
                nft_data["transfer_fee"] = xrp_format_to_nft_fee(nft["TransferFee"])
                nft_data["flags"] = nft["Flags"]
                nft_data["uri"] = validate_hex_to_symbol(nft["URI"])
                created_nfts.append(nft_data)
        return created_nfts

    async def created_taxons(wallet_addr: str, mainnet: bool = True) -> list:
        """return all taxons an account has used to create nfts"""
        taxons = []
        result = (
            requests.get(
                f"https://api.xrpldata.com/api/v1/xls20-nfts/taxon/{wallet_addr}"
            ).json()
            if mainnet
            else requests.get(
                f"https://test-api.xrpldata.com/api/v1/xls20-nfts/taxon/{wallet_addr}"
            ).json()
        )
        if "data" in result and "taxons" in result["data"]:
            taxons = result["data"]["taxons"]
        return taxons

    async def created_nfts_taxon(wallet_addr: str, taxon: int, mainnet: bool = True):
        """return all nfts with similar taxon an account has created"""
        created_nfts = []
        result = (
            requests.get(
                f"https://api.xrpldata.com/api/v1/xls20-nfts/issuer/{wallet_addr}/taxon/{taxon}"
            ).json()
            if mainnet
            else requests.get(
                f"https://test-api.xrpldata.com/api/v1/xls20-nfts/issuer/{wallet_addr}/taxon/{taxon}"
            ).json()
        )
        if "data" in result and "nfts" in result["data"]:
            nfts = result["data"]["nfts"]
            for nft in nfts:
                nft_data = {}
                nft_data["nftoken_id"] = nft["NFTokenID"]
                nft_data["issuer"] = nft["Issuer"]
                nft_data["owner"] = nft["Owner"]
                nft_data["taxon"] = nft["Taxon"]
                nft_data["sequence"] = nft["Sequence"]
                nft_data["transfer_fee"] = xrp_format_to_nft_fee(nft["TransferFee"])
                # nft_data["flags"] = nft["Flags"]
                nft_data["uri"] = validate_hex_to_symbol(nft["URI"])
                created_nfts.append(nft_data)
        return created_nfts


def add_token(
    sender_addr: str,
    token: str,
    issuer: str,
    rippling: bool = False,
    is_lp_token: bool = False,
    fee: str = None,
) -> dict:
    """enable transacting with a token"""
    flag = TrustSetFlag.TF_SET_NO_RIPPLE
    cur = token if is_lp_token else validate_symbol_to_hex(token)
    if rippling:
        flag = TrustSetFlag.TF_CLEAR_NO_RIPPLE
    cur = IssuedCurrencyAmount(currency=cur, issuer=issuer, value=1_000_000_000)
    txn = TrustSet(
        account=sender_addr,
        limit_amount=cur,
        flags=flag,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# can only be called if user empties balance
def remove_token(sender_addr: str, token: str, issuer: str, fee: str = None) -> dict:
    """disable transacting with a token"""
    trustset_cur = IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token), issuer=issuer, value=0
    )
    txn = TrustSet(
        account=sender_addr,
        limit_amount=trustset_cur,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_token_freeze_state(
    sender_addr: str,
    target_addr: str,
    token_name: str,
    freeze: bool = False,
    fee: str = None,
) -> dict:
    """Freeze a token for an account, only the issuer can call this"""
    state = TrustSetFlag.TF_CLEAR_FREEZE
    if freeze:
        state = TrustSetFlag.TF_SET_FREEZE
    cur = IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token_name),
        issuer=target_addr,
        value=1_000_000_000,
    )
    txn = TrustSet(
        account=sender_addr,
        limit_amount=cur,
        flags=state,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def delete_account(
    sender_addr: str,
    receiver_addr: str,
    receiver_destination_tag: str = None,
    fee: str = None,
) -> dict:
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


def modify_domain(sender_addr: str, domain: str, fee: str = None) -> dict:
    """modify the domain of an account"""
    txn = AccountSet(
        account=sender_addr,
        domain=validate_symbol_to_hex(domain),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_token_transfer_fee(sender_addr: str, transfer_fee: float, fee: str = None):
    """modify the transfer fee of a token | account"""
    txn = AccountSet(
        account=sender_addr,
        transfer_rate=transfer_fee_to_xrp_format(transfer_fee),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_ticksize(sender_addr: str, tick_size: int, fee: str = None):
    """modify the ticksize of a token | account"""
    txn = AccountSet(
        account=sender_addr,
        tick_size=tick_size,
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


def modify_email(sender_addr: str, email: str, fee: str = None) -> dict:
    """modify the email of a token | account"""
    txn = AccountSet(
        account=sender_addr,
        email_hash=str_to_hex(email),
        fee=fee,
        memos=mm(),
        source_tag=M_SOURCE_TAG,
    )
    return txn.to_xrpl()


# print(modify_email(
#     "rGiyqjWjhsRZ8FUjBL2k5ciUa2tcptTX9W",
#     "sayhello@badguy.com"
# ))
