from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import ( AccountSet, AccountObjects, TicketCreate,)
from misc import mm
from x_constants import M_SOURCE_TAG



# region POST
def create_ticket(sender_addr: str, ticket_count: int, ticket_seq: int = None, fee: str = None) -> dict:
    """create a ticket - ticket_count = how many ticket =< 250, ticket_seq = the account seq to count from"""
    txn = TicketCreate(account=sender_addr, ticket_count=ticket_count, ticket_sequence= ticket_seq, source_tag=M_SOURCE_TAG, memos=mm(), fee=fee)
    return txn.to_xrpl()

def cancel_ticket(sender_addr: str, ticket_sequence: int, fee: str = None) -> dict:
    """cancel a ticket"""
    txn = AccountSet(account=sender_addr, sequence=ticket_sequence, fee=fee, memos=mm(), source_tag=M_SOURCE_TAG)
    return txn.to_xrpl()

# endregion




# region GET
async def account_tickets(url: str, wallet_addr: str) -> list:
    """return a list tickets created by an account"""
    tickets_ = []
    req = AccountObjects(account=wallet_addr, ledger_index="validated", type="ticket")
    response =  await AsyncJsonRpcClient(url).request(req)
    result = response.result
    if "account_objects" in result:
        account_tickets = result["account_objects"]
        for ticket in account_tickets:
            ticket_data = {}
            ticket_data["ticket_id"] = ticket["index"]
            ticket_data["account"] = ticket["Account"]
            # ticket_data["flags"] = ticket["Flags"]
            ticket_data["ticket_sequence"] = ticket["TicketSequence"]
            tickets_.append(ticket_data)
    return tickets_

# uneccessary
# async def get_ticket_info(url: str, ticket_id: str) -> dict:
#     ticket_info = {}
#     query = LedgerEntry(ledger_index="validated", ticket=ticket_id)
#     response = await AsyncJsonRpcClient(url).request(query)
#     result = response.result
#     if "Account" in result["node"]:
#         ticket_info["index"] = result["node"]["index"]
#         ticket_info["owner"] = result["node"]["Account"]
#         ticket_info["object_type"] = result["node"]["LedgerEntryType"]
#         ticket_info["ticket_sequence"] = result["node"]["TicketSequence"]
#         ticket_info["previous_transaction_id"] = result["node"]["PreviousTxnID"]
#     return ticket_info

# endregion
