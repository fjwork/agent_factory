import httpx
import json
from pydantic import Field

from trail_agent.tools.auth_service import ToolAuthService
from trail_agent.tools.constants import SF_LANGUAGE_CODES, LANGUAGE_EN_US, EINSTEIN_SEARCH_URL
from trail_agent.tools.sf_secrets import get_secret


async def store_standards_tool(
        search_query: str 

    ) -> str:
        """
        This tool is an expert in giving H-E-B Store Standards articles based on search query and language code.
        Any information about H-E-B Store Standards is retrieved from the Salesforce Einstein Search API.
        The tool will return a JSON string containing the search results.
        """

        language_code = LANGUAGE_EN_US
        
        token = get_secret("okta-token-for-salesforce-agent", project_id="heb-dsol-ai-platform-nonprod")
        print(f"got  token from screts manager")

  
        tool_auth_service = ToolAuthService(token)
        access_token = await tool_auth_service.get_salesforce_access_token()
        print(f"generated access token in exchange for okta token")


        async with httpx.AsyncClient() as client:
            response = await client.post(
                EINSTEIN_SEARCH_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "searchTerm": search_query,
                    "page": {"offset": 0, "size": 5, "token": 0},
                    "language": language_code,
                    "filters": {"contentTypes": ["H-E-B Standards"]},
                },
            )

        print(response)

        return {"result":  json.dumps(response.json())}              
