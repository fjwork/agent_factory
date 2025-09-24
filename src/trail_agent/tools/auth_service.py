import httpx

# from cachetools import TTLCache
from fastapi import HTTPException, status
from trail_agent.tools.constants import SALESFORCE_TOKEN_EXCHANGE_HANDLER, SALESFORCE_DOMAIN
from trail_agent.tools.sf_secrets import get_secret

# sf_tool_auth_cache = TTLCache(maxsize=float("inf"), ttl=1800)
cached_token = None  # self.get_cached_salesforce_token(token)

class ToolAuthService:
    def __init__(self, token: str):
        self.token = token

    async def get_salesforce_access_token(self) -> str:
        """Retrieves a Salesforce access token on behalf of the user"""
        # if "Authorization" not in self.request.headers:
        #     log.error("No Authorization Header")
        #     raise HTTPException(detail="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)

        # settings = Settings()
        salesforce_consumer_key = get_secret("SALESFORCE_CONSUMER_KEY", project_id="heb-dsol-ai-platform-nonprod")
        salesforce_consumer_secret = get_secret("SALESFORCE_CONSUMER_SECRET", project_id="heb-dsol-ai-platform-nonprod")
        try:
            # remove Bearer & white space
            token = self.token.replace("Bearer ", "")
            # log.info("*****TOKEN*****", token)
            token_url = f"https://{SALESFORCE_DOMAIN}.salesforce.com/services/oauth2/token"
            # log.info("*****TOKEN URL*****", token_url)
            print(f"Token URL: {token_url}")
            cached_token = None  # self.get_cached_salesforce_token(token)

            if cached_token is not None:
                access_token = cached_token
                print(f"Using cached access token")
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        token_url,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data={
                            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                            "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
                            "subject_token": token,
                            "client_id": salesforce_consumer_key,
                            "client_secret": salesforce_consumer_secret,
                            "scope": "api",
                            "token_handler": SALESFORCE_TOKEN_EXCHANGE_HANDLER,
                        },
                    )
                response.raise_for_status()

                access_token = response.json()["access_token"]
                cached_token = access_token  # sf_tool_auth_cache[token] = access_token
                print(f"Cached access token for future use")                
                # log.info("ACCESS TOKEN", access_token)

                # sf_tool_auth_cache[token] = access_token
        except httpx.HTTPStatusError as e:
            # log.error(f"Salesforce token response error - {e}")
            raise HTTPException(
                detail="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        except httpx.RequestError as e:
            # log.error(f"Salesforce token request error - {e}")
            raise HTTPException(
                detail="Unable to retrieve Salesforce access token",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return access_token

    # def get_cached_salesforce_token(self, token: str):
    #     try:
    #         cached_token = sf_tool_auth_cache[token]

    #         log.info("Found cached Salesforce token")

    #         return cached_token
    #     except KeyError:
    #         log.warning("Key for Salesforce token not in cache")
