from datetime import datetime, timedelta
from decimal import Decimal
from typing import Union

from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import sign, is_valid_message
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.clients import JsonRpcClient
from xrpl.models import (XRP, AccountSet, AccountObjects, DepositPreauth, AccountOffers, BookOffers,
                         CheckCancel, CheckCash, CheckCreate, EscrowCancel,
                         EscrowCreate, EscrowFinish, IssuedCurrency,
                         IssuedCurrencyAmount, TicketCreate, OfferCancel,
                         OfferCreate, Tx, OfferCreateFlag, DepositAuthorized, PaymentChannelCreate,
                         PaymentChannelFund, ChannelVerify, LedgerEntry,
                         PaymentChannelClaim, PaymentChannelClaimFlag, DIDDelete, DIDSet,)
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime, xrp_to_drops, datetime_to_ripple_time

from Misc import mm, validate_hex_to_symbol, validate_symbol_to_hex

from x_constants import M_SOURCE_TAG

"""
Manage Checks, Offers, Escrows,
Deposit authorization, Tickets, XRP Payment channels,
DID


Ripple Path Finding and Payment
MultiSig


Price Oracles
AMM
Escrow - Token, NFT


ticket info
payment channel info
"""



def create_did(sender_addr: str, did_document: str = None, data: str = None, uri:  str = None) -> dict:
    """
    You must include either Data, DIDDocument, or URI.
    If all three fields are missing, the transaction fails.
    data: The public attestations of identity credentials associated with the DID.
    did: The DID document associated with the DID.
    uri: The Universal Resource Identifier associated with the DID.
    """
    txn = DIDSet(
        account=sender_addr, did_document=validate_symbol_to_hex(did_document), data=validate_symbol_to_hex(data), uri=validate_symbol_to_hex(uri))
    return txn.to_xrpl()

def update_did(sender_addr: str, did_document: str = None, data: str = None, uri:  str = None) -> dict:
    """
    You must include either Data, DIDDocument, or URI.
    If all three fields are missing, the transaction fails.
    data: The public attestations of identity credentials associated with the DID.
    did: The DID document associated with the DID.
    uri: The Universal Resource Identifier associated with the DID.
    """
    txn = DIDSet(
        account=sender_addr, did_document=validate_symbol_to_hex(did_document), data=validate_symbol_to_hex(data), uri=validate_symbol_to_hex(uri))
    return txn.to_xrpl()

def delete_did(sender_addr: str) -> dict:
    txn = DIDDelete(account=sender_addr)
    return txn.to_xrpl() 


# settle delay max = 2**32-1 time in seconds, Amount of time the source address must wait before closing the channel if it has unclaimed XRP.
def create_xrp_payment_channel(sender_addr: str, public_key: str, amount: Union[int, float, Decimal], receiver: str, settle_delay: int, cancel_after: int = None, destination_tag: int = None, fee: str = None) -> dict:
    txn = PaymentChannelCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver, settle_delay=settle_delay, public_key=public_key, cancel_after=cancel_after, destination_tag=destination_tag, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def claim_xrp_payment_channel_funds(sender_addr: str, public_key: str, channel_id: str, signature: str, amount: str, fee: str = None) -> dict:
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, signature=signature, amount=xrp_to_drops(amount), balance=xrp_to_drops(amount), public_key=public_key, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# only the payment channel sender can call this - https://xrpl.org/docs/references/protocol/transactions/types/paymentchannelfund/
def update_xrp_payment_channel(sender_addr: str, channel_id: str, amount: Union[int, float, Decimal], expiry_date: int = None, fee: str = None) -> dict:
    txn = PaymentChannelFund(account=sender_addr, channel=channel_id, amount=xrp_to_drops(amount), expiration=expiry_date, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()

def renew_payment_channel(sender_addr: str, channel_id: str, fee: str = None) -> dict:
    """Clear the channel's Expiration time."""
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, flags=PaymentChannelClaimFlag.TF_RENEW, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def close_payment_channel(sender_addr: str, channel_id: str, fee: str = None) -> dict:
    txn = PaymentChannelClaim(account=sender_addr, channel=channel_id, flags=PaymentChannelClaimFlag.TF_CLOSE, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def generate_xrp_payment_channel_signature(channel_id: str, amount: Union[int, Decimal, float], private_key: str) -> str:
    data = encode_for_signing_claim({"channel": channel_id, "amount": xrp_to_drops(amount)})
    return sign(data, private_key)

# def verify_xrp_payment_channel_signature(channel_id: str, amount: Union[int, float, Decimal], public_key: str, signature: str) -> bool:
#     """check the validity of a signature that can be used to redeem a specific amount of XRP from a payment channel."""
#     value = False
#     data = encode_for_signing_claim({"channel": channel_id, "amount": xrp_to_drops(amount)})
#     value = is_valid_message(data, signature, public_key)
#     return value

def create_ticket(sender_addr: str, ticket_count: int, ticket_seq: int = None, fee: str = None) -> dict:
    """create a ticket - ticket_count = how many ticket =< 250, ticket_seq = the account seq to count from"""
    txn = TicketCreate(account=sender_addr, ticket_count=ticket_count, ticket_sequence= ticket_seq, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()

def cancel_ticket(sender_addr: str, ticket_sequence: int, fee: str = None) -> dict:
    """cancel a ticket"""
    txn = AccountSet(account=sender_addr, sequence=ticket_sequence, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def deposit_pre_auth(sender_addr: str, authorize: str = None, unauthorize: str = None, fee: str = None) -> dict:
    """authorize or unauthorize an account to send you payments"""
    txn = DepositPreauth(account=sender_addr, authorize=authorize, unauthorize=unauthorize, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def create_xrp_check(sender_addr: str, receiver_addr: str, amount: Union[int, float, Decimal], expiry_date: int = None, invoice_id: str = None, fee: str = None) -> dict:
    """create xrp check"""
    txn = CheckCreate(account=sender_addr, destination=receiver_addr, send_max=xrp_to_drops(amount), expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG, invoice_id=invoice_id)
    return txn.to_xrpl()

def cash_xrp_check(sender_addr: str, check_id: str, amount: Union[int, Decimal, float], fee: str = None) -> dict:
    """cash a check, only the receiver defined on creation can cash a check"""
    txn = CheckCash(account=sender_addr, check_id=check_id, amount=xrp_to_drops(amount), fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def cancel_check(sender_addr: str, check_id: str, fee: str = None) -> dict:
    """cancel a check"""
    txn = CheckCancel(account=sender_addr, check_id=check_id, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl() 

def create_token_check(sender_addr: str, receiver_addr: str, token: str, amount: str, issuer: str, expiry_date: Union[int, None], fee: str = None) -> dict:
    """create a token check"""
    txn = CheckCreate(account=sender_addr, destination=receiver_addr,
    send_max=IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token), 
        issuer=issuer, 
        value=amount), expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def cash_token_check(sender_addr: str, check_id: str, token: str, amount: str, issuer: str, fee: str = None) -> dict:
    """cash a check, only the receiver defined on creation
    can cash a check"""
    txn = CheckCash(account=sender_addr, check_id=check_id, amount=IssuedCurrencyAmount(
        currency=validate_symbol_to_hex(token),
        issuer=issuer,
        value=amount), fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def create_xrp_escrow(sender_addr: str, amount: Union[int, float, Decimal], receiver_addr: str, condition: Union[str, None], claim_date: Union[int, None], expiry_date: Union[int, None], fee: str = None) -> dict:
    """create an Escrow\n
    fill condition with `Misc.gen_condition_fulfillment["condition"]`\n
    You must use one `claim_date` or `expiry_date` unless this will fail"""
    txn = EscrowCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver_addr, finish_after=claim_date, cancel_after=expiry_date, condition=condition, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def schedule_xrp( sender_addr: str, amount: Union[int, float, Decimal], receiver_addr: str, claim_date: int, expiry_date: Union[int, None], fee: str = None) -> dict:
    """schedule an Xrp payment
    \n expiry date must be greater than claim date"""
    txn = EscrowCreate(account=sender_addr, amount=xrp_to_drops(amount), destination=receiver_addr, finish_after=claim_date, cancel_after=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def r_sequence(client: JsonRpcClient, prev_txn_id: str) -> int:
    """return escrow seq for finishing or cancelling escrow"""
    seq = 0
    req = Tx(transaction=prev_txn_id)
    response = client.request(req)
    result = response.result
    if "Sequence" in result:
        seq = result["Sequence"]
    return seq

def cancel_xrp_escrow(sender_addr: str, escrow_creator: str, prev_txn_id: str, mainnet: bool = True, fee: str = None) -> dict:
    """cancel an escrow\n
    If the escrow does not have a CancelAfter time, it never expires """
    client = JsonRpcClient("https://xrplcluster.com") if mainnet else JsonRpcClient("https://s.altnet.rippletest.net:51234")
    txn = EscrowCancel(account=sender_addr, owner=escrow_creator, offer_sequence=r_sequence(client, prev_txn_id), fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def finish_xrp_escrow(sender_addr: str, escrow_creator: str, prev_txn_id: str, condition: Union[str, None], fulfillment: Union[str, None], mainnet: bool = True, fee: str = None) -> dict:
    """complete an escrow\n
    cannot be called until the finish time is reached"""
    client = JsonRpcClient("https://xrplcluster.com") if mainnet else JsonRpcClient("https://s.altnet.rippletest.net:51234")
    txn = EscrowFinish(account=sender_addr, owner=escrow_creator, offer_sequence=r_sequence(client, prev_txn_id), condition=condition, fulfillment=fulfillment, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

def cancel_offer( sender_addr: str, offer_seq: int, fee: str = None) -> dict:
    """cancel an offer"""
    txn = OfferCancel(account=sender_addr, offer_sequence=offer_seq, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()


def create_offer( sender_addr: str, pay: Union[float, IssuedCurrencyAmount], receive: Union[float, IssuedCurrencyAmount], expiry_date: int = None,
    tf_passive: bool = False, tf_immediate_or_cancel: bool = False, tf_fill_or_kill: bool = False, tf_sell: bool = False, fee: str = None) -> dict:
    """create an offer"""
    flags = []
    if tf_passive:
        flags.append(OfferCreateFlag.TF_PASSIVE)
    if tf_immediate_or_cancel:
        flags.append(OfferCreateFlag.TF_IMMEDIATE_OR_CANCEL)
    if tf_fill_or_kill:
        flags.append(OfferCreateFlag.TF_FILL_OR_KILL)
    if tf_sell:
        flags.append(OfferCreateFlag.TF_SELL)
    txn_dict = {}
    if isinstance(receive, float) and isinstance(pay, IssuedCurrencyAmount): # check if give == xrp and get == asset
        txn = OfferCreate(account=sender_addr, taker_pays=xrp_to_drops(receive), taker_gets=pay, expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG, flags=flags)
        txn_dict = txn.to_xrpl()
    if isinstance(receive, IssuedCurrencyAmount) and isinstance(pay, float): # check if give == asset and get == xrp
        txn = OfferCreate(account=sender_addr, taker_pays=receive, taker_gets=xrp_to_drops(pay), expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG, flags=flags)
        txn_dict = txn.to_xrpl()
    if isinstance(receive, IssuedCurrencyAmount) and isinstance(pay, IssuedCurrencyAmount): # check if give and get are == asset
        txn = OfferCreate(account=sender_addr, taker_pays=receive, taker_gets=pay, expiration=expiry_date, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG, flags=flags)
        txn_dict = txn.to_xrpl()
    return txn_dict



class xObject(AsyncJsonRpcClient):
    def __init__(self, url: str) -> None:
        self.client = AsyncJsonRpcClient(url)

    async def account_did(self, wallet_addr: str) -> dict:
        """show it on the wallet page -  and be like, no did? create one"""
        did = {}
        req = LedgerEntry(ledger_index="validated", did=wallet_addr)
        response = await self.client.request(req)
        result = response.result
        if "index" in result and "Account" in result["node"]:
            did["index"] = result["node"]["index"]
            did["did_document"] = result["node"]["DIDDocument"]
            did["data"] = result["node"]["Data"]
            did["uri"] = result["node"]["URI"]
        return did

    async def verify_xrp_payment_channel_signature(self, channel_id: str, amount: Union[int, float, Decimal], public_key: str, signature: str) -> bool:
        """check the validity of a signature that can be used to redeem a specific amount of XRP from a payment channel."""
        value = False
        req = ChannelVerify(channel_id=channel_id, amount=xrp_to_drops(amount), public_key=public_key, signature=signature)
        response = await self.client.request(req)
        result = response.result
        if "signature_verified" in result:
            value = result["signature_verified"]
        return value    
    
    async def is_deposit_authorized(self, sender_addr: str, receiver_addr: str) -> bool:
        """check if an account is authorized to send xrp to another account"""
        value = False
        req = DepositAuthorized(source_account=sender_addr, destination_account=receiver_addr)
        response = await self.client.request(req)
        result = response.result
        if "deposit_authorized" in result:
            value = result["is_deposit_authorized"]
        return value

    async def account_xrp_payment_channels(self, wallet_addr: str) -> list:
        """return a list of the payment channels created by an account"""
        paymentchannels_ = []
        req = AccountObjects(account=wallet_addr,  type="payment_channel")
        response = await self.client.request(req)
        result = response.result
        if "account_objects" in result:
            account_paymentchannels = result["account_objects"]
            for paymentchannel in account_paymentchannels:
                paymentchannel_data = {}
                paymentchannel_data["channel_id"] = paymentchannel["index"]
                paymentchannel_data["sender"] = paymentchannel["Account"]
                paymentchannel_data["amount_deposited"] = str(drops_to_xrp(paymentchannel["Amount"]))
                paymentchannel_data["amount_paid_out"] = str(drops_to_xrp(paymentchannel["Balance"]))
                paymentchannel_data["amount_remaining"] = str(drops_to_xrp(str(int(paymentchannel["Amount"]) - int(paymentchannel["Balance"]))))
                paymentchannel_data["receiver"] = paymentchannel["Destination"]
                paymentchannel_data["settle_delay"] = str(timedelta(seconds=(paymentchannel["SettleDelay"])))
                paymentchannel_data["public_key"] = paymentchannel["PublicKey"]
                paymentchannel_data["cancel_after_date"] = str(ripple_time_to_datetime(paymentchannel["CancelAfter"])) if "CancelAfter" in paymentchannel else ''
                paymentchannel_data["expiry_date"] = str(ripple_time_to_datetime(paymentchannel["Expiration"])) if "Expiration" in paymentchannel else ''
                paymentchannel_data["destination_tag"] = paymentchannel["DestinationTag"] if "DestinationTag" in paymentchannel else ''
                paymentchannels_.append(paymentchannel_data)
        return paymentchannels_
    
    async def account_tickets(self, wallet_addr: str) -> list:
        """return a list tickets created by an account"""
        tickets_ = []
        req = AccountObjects(account=wallet_addr, ledger_index="validated", type="ticket")
        response = await self.client.request(req)
        result = response.result
        if "account_objects" in result:
            account_tickets = result["account_objects"]
            for ticket in account_tickets:
                ticket_data = {}
                ticket_data["ticket_id"] = ticket["index"]
                ticket_data["account"] = ticket["Account"]
                ticket_data["flags"] = ticket["Flags"]
                ticket_data["ticket_sequence"] = ticket["TicketSequence"]
                tickets_.append(ticket_data)
        return tickets_

    async def account_checks(self, wallet_addr: str) -> list:
        """return a list of checks an account sent or received"""
        checks_= []
        req = AccountObjects(account=wallet_addr, ledger_index="validated", type="check")
        response = await self.client.request(req)
        result = response.result
        if "account_objects" in result:
            account_checks = result["account_objects"]
            for check in account_checks:
                check_data = {}
                check_data["check_id"] = check["index"]
                check_data["sender"] = check["Account"]
                check_data["receiver"] = check["Destination"]
                check_data["expiry_date"] = ""
                if isinstance(check["SendMax"], str):
                    check_data["token"] = "XRP"
                    check_data["issuer"] = ""
                    check_data["amount"] = str(drops_to_xrp(check["SendMax"]))
                if isinstance(check["SendMax"], dict):
                    check_data["token"] = validate_hex_to_symbol(check["SendMax"]["currency"])
                    check_data["issuer"] = check["SendMax"]["issuer"]
                    check_data["amount"] = check["SendMax"]["value"]
                if "Expiration" in check:
                    check_data["expiry_date"] = str(ripple_time_to_datetime(check["Expiration"]))
                checks_.append(check_data)
        return checks_

    async def account_xrp_escrows(self, wallet_addr: str) -> list:
        """returns all account escrows, used for returning scheduled payments"""
        escrows_ = []
        req = AccountObjects(account=wallet_addr, ledger_index="validated", type="escrow")
        response = await self.client.request(req)
        result = response.result
        if "account_objects" in result:
            escrows = result["account_objects"]
            for escrow in escrows:
                if isinstance(escrow["Amount"], str):
                    escrow_data = {}
                    escrow_data["escrow_id"] = escrow["index"]
                    escrow_data["sender"] = escrow["Account"]
                    escrow_data["receiver"] = escrow["Destination"]
                    escrow_data["amount"] = str(drops_to_xrp(escrow["Amount"]))
                    escrow_data["prev_txn_id"] = ""
                    escrow_data["redeem_date"] = ""
                    escrow_data["expiry_date"] = ""
                    escrow_data["condition"] = ""
                    if "PreviousTxnID" in escrow:
                        escrow_data["prev_txn_id"] = escrow["PreviousTxnID"] # needed to cancel or complete the escrow
                    if "FinishAfter" in escrow:
                        escrow_data["redeem_date"] = str(ripple_time_to_datetime(escrow["FinishAfter"]))
                    if "CancelAfter" in escrow:
                        escrow_data["expiry_date"] = str(ripple_time_to_datetime(escrow["CancelAfter"]))
                    if "Condition" in escrow:
                        escrow_data["condition"] = escrow["Condition"]
                    escrows_.append(escrow_data)
        return escrows_

    # async def r_seq_dict(prev_txn_id: str, mainnet: bool = True) -> dict:
    #     """return escrow seq or ticket sequence for finishing or cancelling \n use seq_back_up if seq is null"""
    #     info_dict = {}
    #     info_dict["sequence"] = ""
    #     info_dict["seq_back_up"] = ""
    #     client = AsyncJsonRpcClient("https://xrplcluster.com") if mainnet else AsyncJsonRpcClient("https://s.altnet.rippletest.net:51234")

    #     req = Tx(transaction=prev_txn_id)
    #     response = await self.client.request(req)
    #     result = response.result
    #     if "Sequence" in result:
    #         info_dict["sequence"] = result["Sequence"]
    #     if "TicketSequence" in result:
    #         info_dict["seq_back_up"] = result["TicketSequence"]
    #     return info_dict

    async def account_offers(self, wallet_addr: str) -> list:
        """return all offers an account created"""
        offer_list = []
        req = AccountOffers(account=wallet_addr, ledger_index="validated")
        response = await self.client.request(req)
        result = response.result
        if "offers" in result:
            offers = result["offers"]
            for offer in offers:
                of = {}
                of["flags"] = offer["flags"]
                of["sequence"] = offer["seq"]
                of["quality"] = offer["quality"]# str(drops_to_xrp(offer["quality"])) # rate is subject to error from the blockchain because xrp returned in this call has no decimal  # The exchange rate of the offer, as the ratio of the original taker_pays divided by the original taker_gets. rate = pay/get
                if isinstance(offer["taker_pays"], dict):
                    of["buy_token"] = validate_hex_to_symbol(offer["taker_pays"]["currency"])
                    of["buy_issuer"] = offer["taker_pays"]["issuer"]
                    of["buy_amount"] = offer["taker_pays"]["value"]
                elif isinstance(offer["taker_pays"], str):
                    of["buy_token"] = "XRP"
                    of["buy_issuer"] = ""
                    of["buy_amount"] = str(drops_to_xrp(offer["taker_pays"]))

                if isinstance(offer["taker_gets"], dict):
                    of["sell_token"] = validate_hex_to_symbol(offer["taker_gets"]["currency"])
                    of["sell_issuer"] = offer["taker_gets"]["issuer"]
                    of["sell_amount"] = offer["taker_gets"]["value"]
                elif isinstance(offer["taker_gets"], str):
                    of["sell_token"] = "XRP"
                    of["sell_issuer"] = ""
                    of["sell_amount"] = str(drops_to_xrp(offer["taker_gets"]))

                of["rate"] = float(of["sell_amount"])/float(of["buy_amount"])
                offer_list.append(of)
        return offer_list

    async def all_offers(self, pay: Union[XRP, IssuedCurrency], receive: Union[XRP, IssuedCurrency]) -> list:
        """returns all offers for 2 pairs"""
        all_offers_list = []
        req = BookOffers(taker_gets=pay, taker_pays=receive, ledger_index="validated")
        response = await self.client.request(req)
        result = response.result
        if "offers" in result:
            offers = result["offers"]
            for offer in offers:
                of = {}
                of["creator"] = offer["Account"]
                of["offer_id"] = offer["index"]
                of["sequence"] = offer["Sequence"] # offer id
                of["rate"] = offer["quality"]
                of["flags"] = offer["Flags"]
                of["creator_liquidity"] = ""
                if "owner_funds" in offer and isinstance(offer["TakerGets"], str):
                    of["creator_liquidity"] = f'{float(drops_to_xrp(offer["owner_funds"]))} XRP' # Amount of the TakerGets currency the side placing the offer has available to be traded.
                if "owner_funds" in offer and isinstance(offer["TakerGets"], dict):
                    of["creator_liquidity"] = f'{offer["owner_funds"]}  {validate_hex_to_symbol(offer["TakerGets"]["currency"])}' # Amount of the TakerGets currency the side placing the offer has available to be traded.
                if isinstance(offer["TakerPays"], dict):
                    of["buy_token"] = validate_hex_to_symbol(offer["TakerPays"]["currency"])
                    of["buy_issuer"] = offer["TakerPays"]["issuer"]
                    of["buy_amount"] = offer["TakerPays"]["value"]
                elif isinstance(offer["TakerPays"], str):
                    of["buy_token"] = "XRP"
                    of["buy_issuer"] = ""
                    of["buy_amount"] = str(drops_to_xrp(offer["TakerPays"]))

                if isinstance(offer["TakerGets"], dict):
                    of["sell_token"] = validate_hex_to_symbol(offer["TakerGets"]["currency"])
                    of["sell_issuer"] = offer["TakerGets"]["issuer"]
                    of["sell_amount"] = offer["TakerGets"]["value"]
                elif isinstance(offer["TakerGets"], str):
                    of["sell_token"] = "XRP"
                    of["sell_issuer"] = ""
                    of["sell_amount"] = str(drops_to_xrp(offer["TakerGets"]))
                all_offers_list.append(of)
        return all_offers_list
        

# from xrpl.wallet import Wallet, generate_faucet_wallet

# tw = Wallet("sEdS6V1GG1aU7AF4JiK17z2fneoeXep", 0)
# testnet_url = "https://s.altnet.rippletest.net:51234"
# client = JsonRpcClient(testnet_url)


# print(
#     create_xrp_escrow(
#         "rGiyqjWjhsRZ8FUjBL2k5ciUa2tcptTX9W", 10, "rBoSibkbwaAUEpkehYixQrXp4AqZez9WqA", None, None, None
#     )
# )

# tc = create_token_check(
#     tw.classic_address,
#     "rBZJzEisyXt2gvRWXLxHftFRkd1vJEpBQP",
#     "USD",
#     "10",
#     "rBZJzEisyXt2gvRWXLxHftFRkd1vJEpBQP",
# )

# xc = create_xrp_check(
#     tw.classic_address,
#     "rBZJzEisyXt2gvRWXLxHftFRkd1vJEpBQP",
#     10,
# )

# xe = create_xrp_escrow(
#         tw.classic_address,
#         10,
#     "rBZJzEisyXt2gvRWXLxHftFRkd1vJEpBQP",
# )

# co = create_offer(

# )
    
import asyncio
p = xObject("http://s.altnet.rippletest.net:51234")
# print(asyncio.run(p.account_xrp_payment_channels("rHWF24jTY4pREhMaEoe14LDeyRejV5saY6")))






