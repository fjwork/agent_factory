SF_LANGUAGE_CODES = [
    "zh_CN",
    "zh_TW",
    "da",
    "nl_NL",
    "en_US",
    "fi",
    "fr",
    "de",
    "it",
    "ja",
    "ko",
    "no",
    "pt_BR",
    "ru",
    "es",
    "es_MX",
    "sv",
    "th",
]

LANGUAGE_EN_US = "en_US"

SALESFORCE_DOMAIN="heb--opxlab.sandbox.my"
SALESFORCE_BASE_URL = f"https://{SALESFORCE_DOMAIN}.salesforce.com"
SALESFORCE_FILE_URL = f"https://{SALESFORCE_DOMAIN.removesuffix('.my')}.file.force.com"
SALESFORCE_TOKEN_EXCHANGE_HANDLER="ChatHEB_TokenExchangeHandler"

EINSTEIN_SEARCH_URL = f"{SALESFORCE_BASE_URL}/services/apexrest/ato/v1/search"
