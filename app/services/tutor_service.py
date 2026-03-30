from datetime import datetime, timedelta
from app.graph import GraphClient
from app.config import settings


class TutorService:
    CACHE_MINUTES = 5

    def __init__(self):
        self.graph = GraphClient()
        self._cache = {
            "expires_at": None,
            "site_id": None,
            "tutores": [],
            "tutores_by_dni": {},
            "tutores_by_codigo": {},
            "dim_idioma_map": {},
            "precio_antiguo_map": {},
            "precio_nuevo_map": {},
            "lista_reporte_id": None,
        }

    # =========================
    # CACHE
    # =========================

    def _cache_vigente(self) -> bool:
        exp = self._cache.get("expires_at")
        return exp is not None and datetime.utcnow() < exp

    async def _cargar_cache_maestro(self):
        if self._cache_vigente():
            return

        site_id = await self.graph.get_site_id()

        lista_tutor = await self.graph.get_list_by_name(site_id, settings.LISTA_TUTOR_NAME)
        lista_reporte = await self.graph.get_list_by_name(site_id, settings.LISTA_REPORTE_NAME)
        lista_dim_idioma = await self.graph.get_list_by_name(site_id, settings.LISTA_DIM_IDIOMA_NAME)
        lista_precio_antiguo = await self.graph.get_list_by_name(site_id, settings.LISTA_PRECIO_ANTIGUO_NAME)
        lista_precio_nuevo = await self.graph.get_list_by_name(site_id, settings.LISTA_PRECIO_NUEVO_NAME)

        tutores_raw = await self.graph.get_list_items(site_id, lista_tutor["id"])
        dim_idioma_raw = await self.graph.get_list_items(site_id, lista_dim_idioma["id"])
        precios_antiguos_raw = await self.graph.get_list_items(site_id, lista_precio_antiguo["id"])
        precios_nuevos_raw = await self.graph.get_list_items(site_id, lista_precio_nuevo["id"])

        tutores = []
        tutores_by_dni = {}
        tutores_by_codigo = {}

        for item in tutores_raw:
            tutor = self.mapear_tutor(item.get("fields", {}))
            tutores.append(tutor)

            dni = str(tutor["DNI"]).strip()
            codigo = str(tutor["Codigo"]).strip()

            if dni:
                tutores_by_dni[dni] = tutor
            if codigo:
                tutores_by_codigo[codigo] = tutor

        dim_idioma_map = {}
        for item in dim_idioma_raw:
            fields = item.get("fields", {})
            cod_mod = self._normalizar_valor(fields.get("field_0"))
            cod_idioma = str(fields.get("field_4", "")).strip()

            if cod_mod:
                dim_idioma_map[cod_mod] = cod_idioma

        precio_antiguo_map = {}
        for item in precios_antiguos_raw:
            fields = item.get("fields", {})
            cod_idioma = self._normalizar_valor(fields.get("field_0"))
            precio = self._to_float(fields.get("field_4"))

            if cod_idioma:
                precio_antiguo_map[cod_idioma] = precio

        precio_nuevo_map = {}
        for item in precios_nuevos_raw:
            fields = item.get("fields", {})
            cod_idioma = self._normalizar_valor(fields.get("field_0"))
            precio = self._to_float(fields.get("field_4"))

            if cod_idioma:
                precio_nuevo_map[cod_idioma] = precio

        self._cache = {
            "expires_at": datetime.utcnow() + timedelta(minutes=self.CACHE_MINUTES),
            "site_id": site_id,
            "tutores": tutores,
            "tutores_by_dni": tutores_by_dni,
            "tutores_by_codigo": tutores_by_codigo,
            "dim_idioma_map": dim_idioma_map,
            "precio_antiguo_map": precio_antiguo_map,
            "precio_nuevo_map": precio_nuevo_map,
            "lista_reporte_id": lista_reporte["id"],
        }

    async def obtener_todos_los_reportes(self):
        await self._cargar_cache_maestro()

        site_id = self._cache["site_id"]
        lista_reporte_id = self._cache["lista_reporte_id"]

        reportes_raw = await self.graph.get_list_items(site_id, lista_reporte_id)
        return [self.mapear_reporte(item.get("fields", {})) for item in reportes_raw]

    def mapear_tutor(self, fields: dict) -> dict:
        return {
            "Codigo": fields.get("field_1"),
            "DNI": str(fields.get("field_2", "")).strip(),
            "ApellidoPaterno": fields.get("field_3"),
            "ApellidoMaterno": fields.get("field_4"),
            "Nombres": fields.get("field_5"),
            "TipoTutor": str(fields.get("field_6", "")).strip().upper(),
            "NombreID": fields.get("field_13"),
            "Activo": str(fields.get("field_14", "")).strip(),
        }

    def mapear_reporte(self, fields: dict) -> dict:
        return {
            "FechaReporte": fields.get("FechaReporte"),
            "NombreAlumno": fields.get("NombreAlumno"),
            "Modalidad": fields.get("Modalidad"),
            "Curso": fields.get("Curso"),
            "DNI": str(fields.get("DNI", "")).strip(),
            "HoraInicio": fields.get("HoraInicio"),
            "HoraFin": fields.get("HoraFin"),
        }

    def calcular_duracion_horas(self, inicio, fin):
        if not inicio or not fin:
            return 0
        h1, m1 = map(int, inicio.split(":"))
        h2, m2 = map(int, fin.split(":"))
        return round(((h2*60+m2)-(h1*60+m1))/60, 2)

    def _normalizar_valor(self, v):
        return str(v or "").strip().upper()

    def _to_float(self, v):
        try:
            return float(v)
        except:
            return 0.0

    # =========================
    # DASHBOARD
    # =========================

    async def construir_dashboard(self, dni: str) -> dict:
        await self._cargar_cache_maestro()

        tutor = self._cache["tutores_by_dni"].get(str(dni).strip())
        if not tutor:
            return {"tutor": None, "resumen": {}, "detalle": []}

        precio_map = self._cache["precio_nuevo_map"]
        reportes = await self.obtener_todos_los_reportes()

        detalle = []
        total_horas = 0
        total_estimado = 0

        for r in reportes:
            if r["DNI"] != str(dni).strip():
                continue

            duracion = self.calcular_duracion_horas(r["HoraInicio"], r["HoraFin"])
            precio = 10
            monto = duracion * precio

            total_horas += duracion
            total_estimado += monto

            detalle.append({
                **r,
                "DuracionHoras": duracion,
                "Precio": precio,
                "MontoEstimado": monto,
            })

        # 🔥 ORDENAR POR FECHA
        def parse_fecha(f):
            if not f:
                return datetime.min
            try:
                return datetime.fromisoformat(str(f).replace("Z", ""))
            except:
                return datetime.min

        detalle.sort(key=lambda x: parse_fecha(x["FechaReporte"]))

        return {
            "tutor": tutor,
            "resumen": {
                "totalHoras": total_horas,
                "estimadoTotal": total_estimado
            },
            "detalle": detalle,
        }
