import msal
from app.config import settings

AUTHORITY = f"https://login.microsoftonline.com/{settings.TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

def get_access_token() -> str:
    app = msal.ConfidentialClientApplication(
        client_id=settings.CLIENT_ID,
        authority=AUTHORITY,
        client_credential=settings.CLIENT_SECRET,
    )

    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" not in result:
        raise Exception(f"No se pudo obtener token: {result}")

    return result["access_token"]