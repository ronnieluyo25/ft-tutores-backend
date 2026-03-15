from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.tutor_service import TutorService

app = FastAPI(title="FriendTeacher Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ft-tutores-react.vercel.app",  # ← tu URL de Vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = TutorService()

class LoginRequest(BaseModel):
    usuario: str

@app.get("/health")
async def health():
    return {"ok": True, "message": "Backend operativo"}

@app.post("/login")
async def login(payload: LoginRequest):
    tutor = await service.buscar_tutor(payload.usuario)

    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")

    if str(tutor["Activo"]).strip().lower() not in {"1", "si", "sí", "true"}:
        raise HTTPException(status_code=403, detail="Tutor inactivo")
    
    #Nombre Completo
    nombre = tutor.get("Nombres", "").strip()
    ap_paterno = tutor.get("ApellidoPaterno", "").strip()
    ap_materno = tutor.get("ApellidoMaterno", "").strip()

    nombre_completo = f"{ap_paterno} {ap_materno} {nombre}".strip()

    return {
        "ok": True,
        "tutor": {
            "dni": tutor["DNI"],
            "codigo": tutor["Codigo"],
            "nombre": tutor["NombreID"],
            "nombreCompleto": nombre_completo,
            "tipoTutor": tutor["TipoTutor"],
            "activo": tutor["Activo"],
        }
    }

@app.get("/dashboard/{dni}")
async def dashboard(dni: str):
    resultado = await service.construir_dashboard(dni)

    if not resultado["tutor"]:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")

    return {
        "ok": True,
        "tutor": resultado["tutor"],
        "resumen": resultado["resumen"],
        "detalle": resultado["detalle"],
    }

@app.post("/cache/clear")
async def clear_cache():
    await service.limpiar_cache()
    return {"ok": True, "message": "Cache limpiada"}