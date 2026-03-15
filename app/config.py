import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TENANT_ID = os.getenv("TENANT_ID", "")
    CLIENT_ID = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    GRAPH_BASE_URL = os.getenv("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")

    SHAREPOINT_HOSTNAME = os.getenv("SHAREPOINT_HOSTNAME", "")
    SHAREPOINT_SITE_PATH = os.getenv("SHAREPOINT_SITE_PATH", "")

    LISTA_TUTOR_NAME = os.getenv("LISTA_TUTOR_NAME", "Lista_Tutor")
    LISTA_REPORTE_NAME = os.getenv("LISTA_REPORTE_NAME", "ListaReporte")
    LISTA_PRECIO_ANTIGUO_NAME = os.getenv("LISTA_PRECIO_ANTIGUO_NAME", "Dim_PrecioTutorAntiguo")
    LISTA_PRECIO_NUEVO_NAME = os.getenv("LISTA_PRECIO_NUEVO_NAME", "Dim_PrecioTutorNuevo")
    LISTA_DIM_CURSO_NAME = os.getenv("LISTA_DIM_CURSO_NAME", "Dim_Curso")
    LISTA_DIM_IDIOMA_NAME = os.getenv("LISTA_DIM_IDIOMA_NAME", "Dim_Idioma")

settings = Settings()