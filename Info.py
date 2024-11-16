import asyncio
import requests
from xrpl.asyncio.clients import AsyncJsonRpcClient

from xrpl.models import AccountInfo, LedgerEntry, Tx
from xrpl.models.requests.ledger_entry import Offer
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime

from Misc import (
    validate_hex_to_symbol,
    xrp_format_to_nft_fee,
    xrp_format_to_transfer_fee,
)


class xInfo(AsyncJsonRpcClient):
    def __init__(self, url: str) -> None:
        self.client = AsyncJsonRpcClient(url)

    async def get_payment_channel_info(self, channel_id: str) -> dict:
        pass

    async def get_ticket_info(self, ticket_id: str) -> dict:
        pass

    async def get_account_info(self, wallet_addr: str) -> dict:
        """returns information about an account"""
        account_info = {}
        query = AccountInfo(account=wallet_addr, ledger_index="validated")
        response = await self.client.request(query)
        result = response.result
        if "account_data" in result:
            account_data = result["account_data"]
            account_info["index"] = account_data["index"]
            account_info["address"] = account_data["Account"]
            account_info["balance"] = str(drops_to_xrp(account_data["Balance"]))
            account_info["object_type"] = account_data["LedgerEntryType"]
            account_info["account_objects"] = account_data["OwnerCount"]
            account_info["sequence"] = account_data["Sequence"]
            account_info["flags"] = account_data["Flags"]
            account_info["tick_size"] = 0
            account_info["token_transfer_fee"] = 0.0
            account_info["domain"] = ""
            account_info["email"] = ""
            # call the xWallet.account_flags to populate this page
            if "TickSize" in account_data:
                account_info["tick_size"] = account_data["TickSize"]
            if "TransferRate" in account_data:
                account_info["token_transfer_fee"] = xrp_format_to_transfer_fee(
                    account_data["TransferRate"]
                )
            if "Domain" in account_data:
                account_info["domain"] = validate_hex_to_symbol(account_data["Domain"])
            if "EmailHash" in account_data:
                account_info["email"] = validate_hex_to_symbol(
                    account_data["EmailHash"]
                )
        return account_info

    async def get_offer_info(
        self,
        use_id: bool = False,
        offer_id: str = None,
        offer_creator: str = None,
        sequence: int = None,
    ) -> dict:
        """returns information about an offer
        if use_id is True, make use of only the offer_id param, else use both sequence and creator\n
        either cannot go together
        """
        offer_info = {}

        query = LedgerEntry(
            ledger_index="validated", offer=Offer(account=offer_creator, seq=sequence)
        )
        if use_id:
            query = LedgerEntry(ledger_index="validated", offer=offer_id)
        response = await self.client.request(query)
        result = response.result
        if "node" in result:
            offer_info["offer_id"] = result["index"]
            offer_info["creator"] = result["node"]["Account"]
            offer_info["sequence"] = result["node"]["Sequence"]
            offer_info["object_type"] = result["node"]["LedgerEntryType"]
            offer_info["expiry_date"] = (
                str(ripple_time_to_datetime(result["node"]["Expiration"]))
                if "Expiration" in result["node"]
                else ""
            )
            offer_info["flags"] = result["node"]["Flags"]

            if isinstance(result["node"]["TakerPays"], dict):
                offer_info["buy_token"] = validate_hex_to_symbol(
                    result["node"]["TakerPays"]["currency"]
                )
                offer_info["buy_issuer"] = result["node"]["TakerPays"]["issuer"]
                offer_info["buy_amount"] = result["node"]["TakerPays"]["value"]
            elif isinstance(result["node"]["TakerPays"], str):
                offer_info["buy_token"] = "XRP"
                offer_info["buy_issuer"] = ""
                offer_info["buy_amount"] = str(
                    drops_to_xrp(result["node"]["TakerPays"])
                )

            if isinstance(result["node"]["TakerGets"], dict):
                offer_info["sell_token"] = validate_hex_to_symbol(
                    result["node"]["TakerGets"]["currency"]
                )
                offer_info["sell_issuer"] = result["node"]["TakerGets"]["issuer"]
                offer_info["sell_amount"] = result["node"]["TakerGets"]["value"]
            elif isinstance(result["node"]["TakerGets"], str):
                offer_info["sell_token"] = "XRP"
                offer_info["sell_issuer"] = ""
                offer_info["sell_amount"] = str(
                    drops_to_xrp(result["node"]["TakerGets"])
                )
        return offer_info

    async def get_xrp_escrow_info(self, escrow_id: str) -> dict:
        """returns information about an escrow"""
        escrow_info = {}
        query = LedgerEntry(ledger_index="validated", escrow=escrow_id)
        response = await self.client.request(query)
        result = response.result
        if "Account" in result["node"] and isinstance(result["node"]["Amount"], str):
            escrow_info["index"] = result["index"]
            escrow_info["sender"] = result["node"]["Account"]
            escrow_info["amount"] = str(drops_to_xrp(result["node"]["Amount"]))
            escrow_info["receiver"] = result["node"]["Destination"]
            escrow_info["object_type"] = result["node"]["LedgerEntryType"]
            escrow_info["prev_txn_id"] = ""
            escrow_info["expiry_date"] = ""
            escrow_info["redeem_date"] = ""
            escrow_info["condition"] = ""
            # add support for flags
            if "PreviousTxnID" in result["node"]:
                escrow_info["prev_txn_id"] = result["node"][
                    "PreviousTxnID"
                ]  # needed to cancel or complete the escrow
            if "CancelAfter" in result["node"]:
                escrow_info["expiry_date"] = str(
                    ripple_time_to_datetime(result["node"]["CancelAfter"])
                )
            if "FinishAfter" in result["node"]:
                escrow_info["redeem_date"] = str(
                    ripple_time_to_datetime(result["node"]["FinishAfter"])
                )
            if "Condition" in result["node"]:
                escrow_info["condition"] = result["node"]["Condition"]
        return escrow_info

    async def get_check_info(self, check_id: str) -> dict:
        """returns information on a check"""
        check_info = {}
        query = LedgerEntry(ledger_index="validated", check=check_id)
        response = await self.client.request(query)
        result = response.result
        if "Account" in result["node"]:
            check_info["index"] = result["index"]
            check_info["sender"] = result["node"]["Account"]
            check_info["receiver"] = result["node"]["Destination"]
            check_info["sequence"] = result["node"]["Sequence"]
            check_info["object_type"] = result["node"]["LedgerEntryType"]
            check_info["expiry_date"] = ""
            if "Expiration" in result["node"]:
                check_info["expiry_date"] = str(
                    ripple_time_to_datetime(result["node"]["Expiration"])
                )
            # add support for flags
            if isinstance(result["node"]["SendMax"], str):
                check_info["token"] = "XRP"
                check_info["issuer"] = ""
                check_info["amount"] = str(drops_to_xrp(result["node"]["SendMax"]))
            elif isinstance(result["node"]["SendMax"], dict):
                check_info["token"] = validate_hex_to_symbol(
                    result["node"]["SendMax"]["currency"]
                )
                check_info["issuer"] = result["node"]["SendMax"]["issuer"]
                check_info["amount"] = result["node"]["SendMax"]["value"]
        return check_info

    async def get_token_info(self, issuer: str) -> dict:
        token_info = {}
        query = AccountInfo(account=issuer, ledger_index="validated")
        response = await self.client.request(query)
        result = response.result
        if "account_data" in result:
            account_data = result["account_data"]
            token_info["index"] = account_data["index"]
            token_info["issuer"] = account_data["Account"]
            token_info["tick_size"] = (
                account_data["TickSize"] if "TickSize" in account_data else 0
            )
            token_info["domain"] = (
                validate_hex_to_symbol(account_data["Domain"])
                if "Domain" in account_data
                else ""
            )
            token_info["email"] = (
                validate_hex_to_symbol(account_data["EmailHash"])
                if "EmailHash" in account_data
                else ""
            )
            token_info["transfer_fee"] = (
                xrp_format_to_transfer_fee(account_data["TransferRate"])
                if "TransferRate" in account_data
                else 0
            )
        return token_info

    async def get_nft_info(
        self, nft_id: str, mainnet: bool = True
    ) -> dict:  # external api
        # only works on mainnet
        """returns information about an NFT \n this method uses an external api\n
        will probably only work on mainnet"""
        nft_info = {}
        response = (
            requests.get(
                f"https://api.xrpldata.com/api/v1/xls20-nfts/nft/{nft_id}"
            ).json()
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
            nft_info["flags"] = nft["Flags"]  # parse flags
        return nft_info

    async def get_nft_metadata(self, nft_id: str, mainnet: bool = True):
        """get nft metadata"""
        nft_request = (
            "https://api.xrpldata.com/api/v1/xls20-nfts/nft/" + nft_id
            if mainnet
            else "https://test-api.xrpldata.com/api/v1/xls20-nfts/nft/" + nft_id
        )
        r = requests.get(nft_request)
        uri_metadata = r.json()
        URI = bytearray.fromhex(uri_metadata["data"]["nft"]["URI"]).decode()
        if URI.startswith("https://ipfs.io/"):
            URI_ONXRP = URI.replace("https://ipfs.io/", "https://onxrp.infura-ipfs.io/")
        else:
            URI_ONXRP = URI.replace("ipfs://", "https://onxrp.infura-ipfs.io/ipfs/")
        r = requests.get(URI_ONXRP)
        nft_info = r.json()
        return nft_info

    async def get_nft_offer_info(self, offer_id: str, mainnet: bool = True) -> dict:
        """return information about an nft offer"""
        offer_info = {}
        response = (
            requests.get(
                f"https://api.xrpldata.com/api/v1/xls20-nfts/offer/id/{offer_id}"
            ).json()
            if mainnet
            else requests.get(
                f"https://test-api.xrpldata.com/api/v1/xls20-nfts/offer/id/{offer_id}"
            ).json()
        )
        if "data" in response and isinstance(response["data"]["offer"], dict):
            offer = response["data"]["offer"]
            offer_info["offer_id"] = offer["OfferID"]
            offer_info["nftoken_id"] = offer["NFTokenID"]
            offer_info["owner"] = offer["Owner"]
            offer_info["flags"] = offer["Flags"]
            offer_info["expiry_date"] = ""
            offer_info["Destination"] = ""
            if isinstance(offer["Amount"], str):
                offer_info["token"] = "XRP"
                offer_info["issuer"] = ""
                offer_info["amount"] = str(drops_to_xrp(offer["Amount"]))
            elif isinstance(offer["Amount"], dict):
                offer_info["token"] = validate_hex_to_symbol(
                    offer["Amount"]["currency"]
                )
                offer_info["issuer"] = offer["Amount"]["issuer"]
                offer_info["amount"] = offer["Amount"]["value"]
            if "Destination" in offer:
                offer_info["receiver"] = offer["Destination"]
            if "Expiration" in offer and offer["Expiration"] != None:
                offer["expiry_date"] = str(ripple_time_to_datetime(offer["Expiration"]))
        return offer_info

    async def pay_txn_info(self, txid: str) -> dict:
        """return more information on a single pay transaction"""
        pay_dict = {}
        query = Tx(transaction=txid)
        response = await self.client.request(query)
        result = response.result
        if "Account" in result:
            pay_dict["sender"] = result["Account"]
            pay_dict["receiver"] = result["Destination"]
            if isinstance(result["Amount"], str):
                pay_dict["token"] = "XRP"
                pay_dict["issuer"] = ""
                pay_dict["amount"] = (
                    str(drops_to_xrp(str(result["meta"]["delivered_amount"])))
                    if "delivered_amount" in result["meta"]
                    and isinstance(result["meta"]["delivered_amount"], str)
                    else str(drops_to_xrp(str(result["Amount"])))
                )
            if (
                isinstance(result["Amount"], dict)
                or "delivered_amount" in result["meta"]
                and isinstance(result["meta"]["delivered_amount"], dict)
            ):
                pay_dict["token"] = (
                    validate_hex_to_symbol(
                        result["meta"]["delivered_amount"]["currency"]
                    )
                    if "delivered_amount" in result["meta"]
                    and isinstance(result["meta"]["delivered_amount"], dict)
                    else validate_hex_to_symbol(result["Amount"]["currency"])
                )
                pay_dict["issuer"] = (
                    result["meta"]["delivered_amount"]["issuer"]
                    if "delivered_amount" in result["meta"]
                    and isinstance(result["meta"]["delivered_amount"], dict)
                    else validate_hex_to_symbol(result["Amount"]["issuer"])
                )
                pay_dict["amount"] = (
                    result["meta"]["delivered_amount"]["value"]
                    if "delivered_amount" in result["meta"]
                    and isinstance(result["meta"]["delivered_amount"], dict)
                    else result["Amount"]["value"]
                )
            pay_dict["fee"] = str(drops_to_xrp(result["Fee"]))
            pay_dict["date"] = str(ripple_time_to_datetime(result["date"]))
            pay_dict["txid"] = result["hash"]
            pay_dict["tx_type"] = result["TransactionType"]
            pay_dict["flags"] = (
                result["Flags"] if "Flags" in result else ""
            )  # work on transaction flags later
            pay_dict["sequence"] = result["Sequence"]
            pay_dict["in_ledger"] = result["inLedger"]
            pay_dict["signature"] = result["TxnSignature"]
            pay_dict["index"] = result["meta"]["TransactionIndex"]
            pay_dict["result"] = result["meta"]["TransactionResult"]
            pay_dict["ledger_state"] = result["validated"]
        return pay_dict

    async def txn_status(self, txid: str) -> dict:
        response = ""
        query = Tx(transaction=txid)
        response = await self.client.request(query)
        result = response.result
        if "Account" in result:
            response = result["meta"]["TransactionResult"]
        return response


f = xInfo("https://s.altnet.rippletest.net:51234")
# f = xInfo("https://xrplcluster.com")


# query = Tx(transaction="AFE7DA31F24EA76496489BC23A64C784C46722B6AB4F6AAF447D49CDD3D1B9BA")
# response =  asyncio.run(f.client.request(query))
# print(response.result)

d = asyncio.run(
    f.pay_txn_info(
        "8E6A9E3101B209C36FDB1DE802ED7BE3F25BE7ABCD89A0EA0E1D6CE7E4B6AF4C",
    )
)

print(d)


# print(hex_to_symbol("697066733A2F2F6261666B72656962766961737774696C34777937786A75326432366C3676356F7071627477346F77703579746F6C6E686C6C61686D69736B707434"))
