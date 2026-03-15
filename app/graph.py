import httpx
from app.auth import get_access_token
from app.config import settings

class GraphClient:
    def __init__(self):
        self.base_url = settings.GRAPH_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {get_access_token()}",
            "Accept": "application/json",
        }

    async def get_site(self):
        url = f"{self.base_url}/sites/{settings.SHAREPOINT_HOSTNAME}:{settings.SHAREPOINT_SITE_PATH}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_site_id(self):
        site = await self.get_site()
        return site["id"]

    async def get_lists(self, site_id: str):
        url = f"{self.base_url}/sites/{site_id}/lists"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("value", [])

    async def get_list_by_name(self, site_id: str, list_name: str):
        lists = await self.get_lists(site_id)
        for lst in lists:
            if lst.get("displayName") == list_name:
                return lst
        raise ValueError(f"No se encontró la lista: {list_name}")

    async def get_list_items(self, site_id: str, list_id: str):
        items = []
        url = f"{self.base_url}/sites/{site_id}/lists/{list_id}/items?$expand=fields"

        async with httpx.AsyncClient(timeout=30.0) as client:
            while url:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                items.extend(data.get("value", []))
                url = data.get("@odata.nextLink")

        return items