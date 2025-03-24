M_SOURCE_TAG = 10011001
D_TYPE = "Done-with-Myrkle"
D_DATA = "https://myrkle.app"


# TODO: format neccesary rquests flags or []

XURLS_ = {
    "TESTNET_URL": "https://s.altnet.rippletest.net:51234",
    "MAINNET_URL": "https://xrplcluster.com",
    "TESTNET_TXNS": "https://testnet.xrpl.org/transactions/",
    "MAINNET_TXNS": "https://livenet.xrpl.org/transactions/",
    "MAINNET_ACCOUNT": "https://livenet.xrpl.org/accounts/",
    "TESTNET_ACCOUNT": "https://testnet.xrpl.org/accounts/",
}


NFTOKEN_FLAGS = [
    {
        "flagname": "Issuer Burn",
        "hex": 0x00000001,
        "decimal": 1,
        "description": "Allow the issuer (or an entity authorized by the issuer) to destroy the minted NFToken, This can be done remotely. (The NFToken's owner can always do so.)",
    },
    {
        "flagname": "Only XRP",
        "hex": 0x00000002,
        "decimal": 2,
        "description": "This NFToken can only be bought or sold for XRP. This can be desirable if the token has a transfer fee and the issuer does not want to receive fees in non-XRP currencies.",
    },
    {
        "flagname": "Transferable",
        "hex": 0x00000008,
        "decimal": 8,
        "description": "This NFToken can be transferred to others. If this flag is not enabled, the token can still be transferred from or to the issuer.",
    },
]

NFTOKEN_OFFER_FLAGS = [
    {
        "flagname": "tfSellNFToken",
        "hex": 0x00000001,
        "decimal": 1,
        "description": "If enabled, the offer is a sell offer. Otherwise, the offer is a buy offer.",
    },
]

PAYMENT_FLAGS = [
    {
        "flagname": "No Direct Ripple",
        "tf": "tfNoDirectRipple",
        "hex": 0x00010000,
        "decimal": 65536,
        "description": "Do not use the default path; only use paths included in the Paths field. This is intended to force the transaction to take arbitrage opportunities. Most clients do not need this.",
    },
    {
        "flagname": "Partial Payment",
        "tf": "tfPartialPayment",
        "hex": 0x00020000,
        "decimal": 131072,
        "description": "The partial payment flag allows a payment to succeed by reducing the amount received.",
    },
    {
        "flagname": "Limit Quality",
        "tf": "tfLimitQuality",
        "hex": 0x00040000,
        "decimal": 262144,
        "description": "The Limit quality flag allows you to set a minimum quality of conversions that you are willing to take.",
    },
]


OFFER_FLAGS = [
    {
        "flagname": "Passive Offer",
        "tf": "tfPassive",
        "hex": 0x00010000,
        "decimal": 65536,
        "description": "If enabled, the Offer does not consume Offers that exactly match it, and instead becomes an Offer object in the ledger. It still consumes Offers that cross it.",
    },
    {
        "flagname": "Immediate or Cancel Offer",
        "tf": "tfImmediateOrCancel",
        "hex": 0x00020000,
        "decimal": 131072,
        "description": "Treat the Offer as an Immediate or Cancel order . The Offer never creates an Offer object in the ledger: it only trades as much as it can by consuming existing Offers at the time the transaction is processed. If no Offers match, it executes 'successfully' without trading anything. In this case, the transaction still uses the result code tesSUCCESS.",
    },
    {
        "flagname": "Fill Or Kill",
        "tf": "tfFillOrKill",
        "hex": 0x00040000,
        "decimal": 131072,
        "description": "Treat the offer as a Fill or Kill order . The Offer never creates an Offer object in the ledger, and is canceled if it cannot be fully filled at the time of execution. By default, this means that the owner must receive the full TakerPays amount; if the tfSell flag is enabled, the owner must be able to spend the entire TakerGets amount instead.",
    },
    {
        "flagname": "Sell All",
        "tf": "tfSell",
        "hex": 0x00080000,
        "decimal": 524288,
        "description": "Exchange the entire TakerGets amount, even if it means obtaining more than the TakerPays amount in exchange.",
    },
]


ACCOUNT_ROOT_FLAGS = [
    {
        "flagname": "Free Regular Key Transaction",
        "hex": 0x00010000,
        "decimal": 65536,
        "asf": "",
        "description": "This account has used its free SetRegularKey transaction.",
    },
    #
    {
        "flagname": "Default Ripple",
        "hex": 0x00800000,
        "decimal": 8388608,
        "asf": "asfDefaultRipple",
        "description": "Enable rippling on this account's trust lines by default. Required for issuing addresses; discouraged for others.",
    },
    {
        "flagname": "Deposit Authorization",
        "hex": 0x01000000,
        "decimal": 16777216,
        "asf": "asfDepositAuth",
        "description": "This account can only receive funds from transactions it initiates, and from [preauthorized accounts](link to deposit preauth).",
    },
    {
        "flagname": "Disable Master Key",
        "hex": 0x00100000,
        "decimal": 1048576,
        "asf": "asfDisableMaster",
        "description": "Disallow the use of the master key to sign transactions for this account. Can only be enabled if the account has configured another way to sign transactions, such as a Regular Key or a Signer List.",
    },
    {
        "flagname": "Block Incoming Checks",
        "hex": 0x08000000,
        "decimal": 134217728,
        "asf": "asfDisallowIncomingCheck",
        "description": "No account should create checks directed to this account.",
    },
    {
        "flagname": "Block Incoming NFTokenOffers",
        "hex": 0x04000000,
        "decimal": 134217728,
        "asf": "asfDisallowIncomingNFTokenOffer",
        "description": "No account should create nft offers directed to this account.",
    },
    {
        "flagname": "Block Incoming Payment Channnels",
        "hex": 0x10000000,
        "decimal": 268435456,
        "asf": "asfDisallowIncomingPayChan",
        "description": "No account should create payment channels directed to this account.",
    },
    {
        "flagname": "Block Incoming Trustlines",
        "hex": 0x20000000,
        "decimal": 536870912,
        "asf": "asfDisallowIncomingTrustline",
        "description": "No account should create trustlines directed to this account.",
    },
    {
        "flagname": "Block XRP",
        "hex": 0x00080000,
        "decimal": 524288,
        "asf": "asfDisallowXRP",
        "description": "No account should send XRP to this account. Not enforced by the blockchain.",
    },
    {
        "flagname": "Global Freeze",
        "hex": 0x00400000,
        "decimal": 4194304,
        "asf": "asfGlobalFreeze",
        "description": "Freeze all assets issued by this account",
    },
    {
        "flagname": "No Freeze",
        "hex": 0x00200000,
        "decimal": 2097152,
        "asf": "asfNoFreeze",
        # "description": "This address cannot freeze trust lines connected to it. Once enabled, cannot be disabled.",
        "description": "Permanently give up the ability to freeze individual trust lines or modify Global Freeze. This flag can never be disabled after being enabled.",
    },
    {
        "flagname": "Require Authorization",
        "hex": 0x00040000,
        "decimal": 262144,
        "asf": "asfRequireAuth",
        "description": "This account must individually approve any account that wants to hold tokens it issues. Can only be enabled if this account has no trust lines connected to it.",
        # "description": "Require authorization for users to hold balances issued by this address. Can only be enabled if the address has no trust lines connected to it."
    },
    {
        "flagname": "Require Destination Tag",
        "hex": 0x00020000,
        "decimal": 131072,
        "asf": "asfRequireDest",
        "description": "Requires incoming payments to this account to specify a Destination Tag.",
    },
    {
        "flagname": "Trustline Clawback",
        "hex": 0x80000000,
        "decimal": 2147483648,
        "asf": "asfAllowTrustLineClawback",
        "description": "This account can claw back tokens it has issued. Can only be set if the account has an empty owner directory (no trust lines, offers, escrows, payment channels, checks, or signer lists, etc). Once enabled it cannot be disabled.",
    },
    # they likely won't supposed to show up
    # {
    #     "flagname": "Authorize NFToken Minter",
    #     "hex": 0x00020000,
    #     "decimal": 131072,
    #     "asf": "asfAuthorizedNFTokenMinter",
    #     "description": "Allow another account to mint non-fungible tokens (NFTokens) on this account's behalf."
    # },
    # {
    #     "flagname": "Account Transaction ID",
    #     "hex": 0x00020000,
    #     "decimal": 131072,
    #     "asf": "asfAccountTxnID",
    #     "description": "Track the ID of this account's most recent transaction. Required for AccountTxnID"
    # },
    # {
    #     "flagname": "lsfAMM",
    #     "hex": 0x02000000,
    #     "decimal": 33554432,
    #     "asf": "",
    #     "description": "This account is an Automated Market Maker instance.",
    # },
]


MPTOKEN_ISSUANCE_FLAGS = [
    {
        "flagname": "Locked",
        "hex": 0x00000001,
        "decimal": int("0x00000001", 16),
        "lsf": "lsfMPTLocked",
        "description": "If set, indicates that all balances are locked.",
    },
    {
        "flagname": "Can Lock",
        "hex": 0x00000002,
        "decimal": int("0x00000002", 16),
        "lsf": "lsfMPTCanLock",
        "description": "If set, indicates that the issuer can lock an individual balance or all balances of this MPT. If not set, the MPT cannot be locked in any way.",
    },
    {
        "flagname": "Requires Authorization",
        "hex": 0x00000004,
        "decimal": int("0x00000004", 16),
        "lsf": "lsfMPTRequireAuth",
        "description": "If set, indicates that individual holders must be authorized. This enables issuers to limit who can hold their assets.",
    },
    {
        "flagname": "Can Escrow",
        "hex": 0x00000008,
        "decimal": int("0x00000008", 16),
        "lsf": "lsfMPTCanEscrow",
        "description": "If set, indicates that individual holders can place their balances into an escrow.",
    },
    {
        "flagname": "Can Trade",
        "hex": 0x00000010,
        "decimal": int("0x00000010", 16),
        "lsf": "lsfMPTCanTrade",
        "description": "If set, indicates that individual holders can trade their balances using the XRP Ledger DEX or AMM.",
    },
    {
        "flagname": "Can Transfer",
        "hex": 0x00000020,
        "decimal": int("0x00000020", 16),
        "lsf": "lsfMPTCanTransfer",
        "description": "If set, indicates that individual holders must be authorized. This enables issuers to limit who can hold their assets.",
    },
    {
        "flagname": "Can Clawback",
        "hex": 0x00000040,
        "decimal": int("0x00000040", 16),
        "lsf": "lsfMPTCanClawback",
        "description": "If set, indicates that the issuer may use the Clawback transaction to claw back value from individual holders.",
    },
]


MPTOKEN_FLAGS = [
    {
        "flagname": "Locked",
        "hex": 0x00000001,
        "decimal": int("0x00000001", 16),
        "lsf": "lsfMPTLocked",
        "description": "If enabled, indicates that the MPT owned by this account is currently locked and cannot be used in any XRP transactions other than sending value back to the issuer.",
    },
    {
        "flagname": "Authorized",
        "hex": 0x00000002,
        "decimal": int("0x00000002", 16),
        "lsf": "lsfMPTAuthorized",
        "description": "If set, indicates that the issuer has authorized the holder for the MPT. This flag can be set using a MPTokenAuthorize transaction; it can also be 'un-set' using a MPTokenAuthorize transaction specifying the tfMPTUnauthorize flag.",
    },
]
