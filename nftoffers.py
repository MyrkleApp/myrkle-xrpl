import asyncio
import requests
from xrpl.asyncio.clients import AsyncJsonRpcClient

from xrpl.models import AccountInfo, LedgerEntry, Tx
from xrpl.models.requests.ledger_entry import Offer
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime

from misc import (
    validate_hex_to_symbol,
    xrp_format_to_nft_fee,
    xrp_format_to_transfer_fee,
)
from x_constants import NFTOKEN_OFFER_FLAGS
import asyncio
from typing import Union
from xrpl.asyncio.clients import AsyncJsonRpcClient
import requests
from xrpl.clients import JsonRpcClient
from xrpl.models import (AccountObjects, IssuedCurrencyAmount, NFTBuyOffers,
                         NFTokenAcceptOffer, NFTokenCancelOffer,
                         NFTokenCreateOffer, NFTokenCreateOfferFlag,
                         NFTSellOffers)
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime, xrp_to_drops

from misc import mm
from x_constants import M_SOURCE_TAG

# region POST
def create_nft_sell_offer(sender_addr: str, nftoken_id: str, get: Union[float, IssuedCurrencyAmount], expiry_date: int = None, receiver: str = None, fee: str = None) -> dict:
    """create an nft sell offer, receiver is the account you want to match this offer"""
    amount = get
    if isinstance(get, float):
        amount = xrp_to_drops(get)
    txn = NFTokenCreateOffer(
        account=sender_addr,
        nftoken_id=nftoken_id,
        amount=amount,
        expiration=expiry_date,
        destination=receiver,
        flags=NFTokenCreateOfferFlag.TF_SELL_NFTOKEN, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_dict()

def create_nft_buy_offer(sender_addr: str, nftoken_id: str, give: Union[float, IssuedCurrencyAmount], expiry_date: int = None, receiver: str = None, fee: str = None) -> dict:
    """create an nft buy offer, receiver is the account you want to match this offer"""
    amount = give
    if isinstance(give, float):
        amount = xrp_to_drops(give)
    txn = NFTokenCreateOffer(
        account=sender_addr,
        nftoken_id=nftoken_id,
        amount=amount,
        expiration=expiry_date,
        destination=receiver, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()   

def accept_nft_offer(sender_addr: str, sell_offer_id: str = None, buy_offer_id: str = None, broker_fee: Union[IssuedCurrencyAmount, float] = None, fee: str = None) -> dict:
    """accept an nft sell or buy offer, or both simultaneously and charge a fee"""
    amount = broker_fee
    if isinstance(broker_fee, float):
        amount = xrp_to_drops(broker_fee)
    txn = NFTokenAcceptOffer(
        account=sender_addr,
        nftoken_buy_offer=buy_offer_id,
        nftoken_sell_offer=sell_offer_id,
        nftoken_broker_fee=amount, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl() 

def cancel_nft_offer(sender_addr: str, nftoken_offer_ids: list[str], fee: str = None) -> dict:
    """cancel offer, pass offer or offers id in a list"""
    txn = NFTokenCancelOffer(
        account=sender_addr,
        nftoken_offers=nftoken_offer_ids, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl() 

# endregion




# region GET

def parse_nft_offer_flags(offer_flag: int) -> list:
    flags = []
    for flag in NFTOKEN_OFFER_FLAGS:
        if flag["hex"] & offer_flag == flag["hex"]:
            flags.append(flag)
    return flag

async def account_nft_offers(url: str, wallet_addr: str, mainnet: bool = True) -> dict:
    """return all nft offers an account has created and received"""
    offers = []

    req = AccountObjects(account=wallet_addr, type="nft_offer")
    response = await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        nft_offers = result["account_objects"]
        for nft_offer in nft_offers:
            offer = {}
            offer["offer_id"] = nft_offer["index"]
            offer["nftoken_id"] = nft_offer["NFTokenID"]
            offer["owner"] = nft_offer["Owner"]
            offer["flag"] = parse_nft_offer_flags(nft_offer["Flags"])
            offer["receiver"] = ""
            offer["expiry_date"] = ""
            if isinstance(nft_offer["Amount"], str):
                offer["token"] = "XRP"
                offer["issuer"] = ""
                offer["amount"] = str(drops_to_xrp(nft_offer["Amount"]))
            if isinstance(nft_offer["Amount"], dict):
                offer["token"] = nft_offer["Amount"]["currency"]
                offer["issuer"] = nft_offer["Amount"]["issuer"]
                offer["amount"] = nft_offer["Amount"]["value"]
            if "Destination" in nft_offer:
                offer["receiver"] = nft_offer["Destination"]
            if "Expiration" in nft_offer:
                offer["expiry_date"] = str(ripple_time_to_datetime(nft_offer["Expiration"]))
            offers.append(offer)
    return offers

async def all_nft_offers(url: str, nftoken_id: str) -> dict:
    """return all available nft offers to buy and sell an nft"""
    offer_dict = {}
    buy = []
    sell = []
    buy_req = NFTBuyOffers(nft_id=nftoken_id, id="validated")
    buy_response = await AsyncJsonRpcClient(url).request(buy_req)
    buy_result = buy_response.result
    if "offers" in buy_result:
        buy_offers = buy_result["offers"]
        for buy_offer in buy_offers:
            offer = {}
            offer["offer_id"] = buy_offer["nft_offer_index"]
            offer["nftoken_id"] = buy_result["nft_id"]
            offer["owner"] = buy_offer["owner"]
            offer["flag"] = buy_offer["flags"]
            offer["expiry_date"] = ""
            offer["receiver"] = ""
            if isinstance(buy_offer["amount"], str):
                offer["token"] = "XRP"
                offer["issuer"] = ""
                offer["amount"] = str(drops_to_xrp(buy_offer["Amount"]))
            if isinstance(buy_offer["amount"], dict):
                offer["token"] = buy_offer["amount"]["currency"]
                offer["issuer"] = buy_offer["amount"]["issuer"]
                offer["amount"] = buy_offer["amount"]["value"]
            if "Destination" in buy_offer:
                offer["receiver"] = buy_offer["Destination"]
            if "Expiration" in buy_offer:
                offer["expiry_date"] = str(ripple_time_to_datetime(buy_offer["Expiration"]))
            buy.append(offer)

    sell_req = NFTSellOffers(nft_id=nftoken_id, id="validated")
    sell_response = await AsyncJsonRpcClient(url).request(sell_req)
    sell_result = sell_response.result
    if "offers" in sell_result:
        sell_offers = sell_result["offers"]
        for sell_offer in sell_offers:
            offer = {}
            offer["offer_id"] = sell_offer["nft_offer_index"]
            offer["nftoken_id"] = sell_result["nft_id"]
            offer["owner"] = sell_offer["owner"]
            offer["flag"] = sell_offer["flags"]
            offer["expiry_date"] = ""
            offer["receiver"] = ""
            if isinstance(sell_offer["amount"], str):
                offer["token"] = "XRP"
                offer["issuer"] = ""
                offer["amount"] = str(drops_to_xrp(sell_offer["amount"]))
            if isinstance(sell_offer["amount"], dict):
                offer["token"] = sell_offer["amount"]["currency"]
                offer["issuer"] = sell_offer["amount"]["issuer"]
                offer["amount"] = sell_offer["amount"]["value"]
            if "destination" in sell_offer:
                offer["receiver"] = sell_offer["destination"]
            if "expiration" in sell_offer:
                offer["expiry_date"] = str(ripple_time_to_datetime(sell_offer["expiration"]))
            sell.append(offer)

    offer_dict["buy"] = buy
    offer_dict["sell"] = sell
    return offer_dict


# external
async def nft_offer_info(offer_id: str, mainnet: bool = True) -> dict:
    """return information about an nft offer"""
    offer_info = {}
    response = requests.get(f"https://api.xrpldata.com/api/v1/xls20-nfts/offer/id/{offer_id}").json() if mainnet else requests.get(f"https://test-api.xrpldata.com/api/v1/xls20-nfts/offer/id/{offer_id}").json()
    if "data" in response and isinstance(response["data"]["offer"], dict):
        offer = response["data"]["offer"]
        offer_info["offer_id"] = offer["OfferID"]
        offer_info["nftoken_id"] = offer["NFTokenID"]
        offer_info["owner"] = offer["Owner"]
        offer_info["flags"] = parse_nft_offer_flags(offer["Flags"])
        offer_info["expiry_date"] = ""
        offer_info["Destination"] = ""
        if isinstance(offer["Amount"], str):
            offer_info["token"] = "XRP"
            offer_info["issuer"] = ""
            offer_info["amount"] = str(drops_to_xrp(offer["Amount"]))
        elif isinstance(offer["Amount"], dict):
            offer_info["token"] = validate_hex_to_symbol(offer["Amount"]["currency"])
            offer_info["issuer"] = offer["Amount"]["issuer"]
            offer_info["amount"] = offer["Amount"]["value"]
        if "Destination" in offer:
            offer_info["receiver"] = offer["Destination"]
        if "Expiration" in offer and offer["Expiration"] != None:
            offer["expiry_date"] = str(ripple_time_to_datetime(offer["Expiration"]))
    return offer_info



# endregion