import os
import msal
import httpx
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GRAPH_BASE_URL = os.getenv("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")

SITE_ID = "friendteacher.sharepoint.com,54bd09f1-a3ba-4c96-87e9-b70a823bf7af,21616dbb-fa12-46a6-9afb-97985cc2701c"
PRECIO_NUEVO_ID = "23a7a035-d87d-47d1-ba76-11559dbb6a5b"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

def get_token():
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" not in result:
        raise Exception(f"Error obteniendo token: {result}")

    return result["access_token"]

async def main():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{GRAPH_BASE_URL}/sites/{SITE_ID}/lists/{PRECIO_NUEVO_ID}/items?$expand=fields&$top=10"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        print("STATUS ITEMS:", resp.status_code)
        print(resp.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())