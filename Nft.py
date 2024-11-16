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

from Misc import mm
from x_constants import M_SOURCE_TAG

"""nft handler"""



def create_sell_offer(sender_addr: str, nftoken_id: str, get: Union[float, IssuedCurrencyAmount], expiry_date: int = None, receiver: str = None, fee: str = None) -> dict:
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




def create_buy_offer(sender_addr: str, nftoken_id: str, give: Union[float, IssuedCurrencyAmount], expiry_date: int = None, receiver: str = None, fee: str = None) -> dict:
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

def cancel_nft_offer(sender_addr: str, nftoken_offer_ids: list[str], fee: str = None) -> dict:
    """cancel offer, pass offer or offers id in a list"""
    txn = NFTokenCancelOffer(
        account=sender_addr,
        nftoken_offers=nftoken_offer_ids, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
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

class xNFT(AsyncJsonRpcClient):
    def __init__(self, url: str) -> None:
        self.client = AsyncJsonRpcClient(url)

    async def account_nft_offers(self, wallet_addr: str, mainnet: bool = True) -> dict:
        """return all nft offers an account has created and received"""
        offers = []

        req = AccountObjects(account=wallet_addr, type="nft_offer")
        response = await self.client.request(req)
        result = response.result
        if "account_objects" in result:
            nft_offers = result["account_objects"]
            for nft_offer in nft_offers:
                offer = {}
                offer["offer_id"] = nft_offer["index"]
                offer["nftoken_id"] = nft_offer["NFTokenID"]
                offer["owner"] = nft_offer["Owner"]
                offer["flag"] = nft_offer["Flags"]
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
    
    # async def account_nft_offers(self, wallet_addr: str, mainnet: bool = True) -> dict:
    #     """return all nft offers an account has created and received"""
    #     created_buy = []
    #     created_sell = []
    #     received_buy = []
    #     received_sell = []
    #     offer_dict = {}

    #     req = AccountObjects(account=wallet_addr, type="nft_offer")
    #     response = await self.client.request(req)
    #     result = response.result
    #     if "account_objects" in result:
    #         nft_offers = result["account_objects"]
    #         for nft_offer in nft_offers:
    #             offer = {}
    #             offer["offer_id"] = nft_offer["index"]
    #             offer["nftoken_id"] = nft_offer["NFTokenID"]
    #             offer["owner"] = nft_offer["Owner"]
    #             offer["flag"] = nft_offer["Flags"]
    #             offer["receiver"] = ""
    #             offer["expiry_date"] = ""
    #             if isinstance(nft_offer["Amount"], str):
    #                 offer["token"] = "XRP"
    #                 offer["issuer"] = ""
    #                 offer["amount"] = str(drops_to_xrp(nft_offer["Amount"]))
    #             if isinstance(nft_offer["Amount"], dict):
    #                 offer["token"] = nft_offer["Amount"]["currency"]
    #                 offer["issuer"] = nft_offer["Amount"]["issuer"]
    #                 offer["amount"] = nft_offer["Amount"]["value"]
    #             if "Destination" in nft_offer:
    #                 offer["receiver"] = nft_offer["Destination"]
    #             if "Expiration" in nft_offer:
    #                 offer["expiry_date"] = str(ripple_time_to_datetime(nft_offer["Expiration"]))
                
    #             if offer["flag"] == 1:
    #                 created_sell.append(offer)
    #             if offer["flag"] == 0:
    #                 created_buy.append(offer)
    #     offer_dict["created_sell"] = created_sell
    #     offer_dict["created_buy"] = created_buy

    #     """return all offers with wallet addr as the 'destination/receiver"""
    #     result = requests.get(f"https://api.xrpldata.com/api/v1/xls20-nfts/offers/offerdestination/{wallet_addr}").json() if mainnet else requests.get(f"https://test-api.xrpldata.com/api/v1/xls20-nfts/offers/offerdestination/{wallet_addr}").json()
    #     if "data" in result and isinstance(result["data"], dict):
    #         account_offers = result["data"]["offers"]
    #         for account_offer in account_offers:
    #             offer = {}
    #             offer["offer_id"] = account_offer["OfferID"]
    #             offer["nftoken_id"] = account_offer["NFTokenID"]
    #             offer["owner"] = account_offer["Owner"]
    #             offer["flag"] = account_offer["Flags"]
    #             offer["receiver"] = ""
    #             offer["expiry_date"] = 0
    #             if isinstance(account_offer["Amount"], str):
    #                 offer["token"] = "XRP"
    #                 offer["issuer"] = ""
    #                 offer["amount"] = str(drops_to_xrp(account_offer["Amount"]))
    #             if isinstance(account_offer["Amount"], dict):
    #                 offer["token"] = account_offer["Amount"]["currency"]
    #                 offer["issuer"] = account_offer["Amount"]["issuer"]
    #                 offer["amount"] = account_offer["Amount"]["value"]
    #             if "Destination" in account_offer:
    #                 offer["receiver"] = account_offer["Destination"]
    #             if "Expiration" in account_offer and account_offer["Expiration"] != None:
    #                 offer["expiry_date"] = str(ripple_time_to_datetime(account_offer["Expiration"]))
                
    #             if offer["flag"] == 1:
    #                 received_sell.append(offer)
    #             if offer["flag"] == 0:
    #                 received_buy.append(offer)
    #     offer_dict["received_sell"] = received_sell
    #     offer_dict["received_buy"] = received_buy
    #     return offer_dict

    async def all_nft_offers(self, nftoken_id: str) -> dict:
        """return all available nft offers to buy and sell an nft"""
        offer_dict = {}
        buy = []
        sell = []
        buy_req = NFTBuyOffers(nft_id=nftoken_id, id="validated")
        buy_response = await self.client.request(buy_req)
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
        sell_response = await self.client.request(sell_req)
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
    


client = AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234")
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
d = xNFT(client.url)
# d = xNFT("https://xrplcluster.com")

# sell_response = client.request(NFTSellOffers(nft_id="00080000ADFDB77A8B3A255EB4DEC33759232E724309D0700000099A00000000", id="validated"))
# sell_result = sell_response.result
# print(sell_result)



print(asyncio.run(  d.account_nft_offers(
    "rGiyqjWjhsRZ8FUjBL2k5ciUa2tcptTX9W", False
)))