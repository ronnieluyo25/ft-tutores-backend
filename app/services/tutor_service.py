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

    async def limpiar_cache(self):
        self._cache["expires_at"] = None

    # =========================
    # MAPEOS
    # =========================

    def mapear_tutor(self, fields: dict) -> dict:
        return {
            "Codigo": fields.get("field_1"),
            "DNI": str(fields.get("field_2", "")).strip(),
            "ApellidoPaterno": fields.get("field_3"),
            "ApellidoMaterno": fields.get("field_4"),
            "Nombres": fields.get("field_5"),
            "TipoTutor": str(fields.get("field_6", "")).strip().upper(),
            "FechaNacimiento": fields.get("field_7"),
            "Edad": fields.get("field_8"),
            "Celular": fields.get("field_9"),
            "Correo": fields.get("field_10"),
            "DiaCumpleaños": fields.get("field_11"),
            "MesCumpleaños": fields.get("field_12"),
            "NombreID": fields.get("field_13"),
            "Activo": str(fields.get("field_14", "")).strip(),
        }

    def mapear_reporte(self, fields: dict) -> dict:
        return {
            "FechaRegistro": fields.get("FechaRegistro"),
            "NombreTutor": fields.get("NombreTutor"),
            "NombreAlumno": fields.get("NombreAlumno"),
            "Modalidad": fields.get("Modalidad"),
            "FechaReporte": fields.get("FechaReporte"),
            "TipoReporte": fields.get("TipoReporte"),
            "Curso": fields.get("Curso"),
            "DuracionClase": fields.get("DuracionClase"),
            "UsoMovilidad": fields.get("UsoMovilidad"),
            "DNI": str(fields.get("DNI", "")).strip(),
            "HoraInicio": fields.get("HoraInicio"),
            "HoraFin": fields.get("HoraFin"),
            "TemasRealizados": fields.get("TemasRealizados"),
            "TareasRealizadas": fields.get("TareasRealizadas"),
            "ActitudEstudiante": fields.get("ActitudEstudiante"),
            "LogrosEstudiante": fields.get("LogrosEstudiante"),
            "Recomendacion": fields.get("Recomendacion"),
        }

    # =========================
    # BÚSQUEDAS
    # =========================

    async def buscar_tutor(self, usuario: str):
        await self._cargar_cache_maestro()
        usuario = str(usuario).strip()

        tutor = self._cache["tutores_by_dni"].get(usuario)
        if tutor:
            return tutor

        tutor = self._cache["tutores_by_codigo"].get(usuario)
        if tutor:
            return tutor

        return None

    async def obtener_todos_los_reportes(self):
        await self._cargar_cache_maestro()

        site_id = self._cache["site_id"]
        lista_reporte_id = self._cache["lista_reporte_id"]

        reportes_raw = await self.graph.get_list_items(site_id, lista_reporte_id)
        return [self.mapear_reporte(item.get("fields", {})) for item in reportes_raw]

    # =========================
    # UTILIDADES
    # =========================

    def _parse_hora_a_minutos(self, hora_str: str) -> int | None:
        if not hora_str:
            return None

        hora_str = str(hora_str).strip()
        formatos = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]

        for fmt in formatos:
            try:
                dt = datetime.strptime(hora_str, fmt)
                return dt.hour * 60 + dt.minute
            except ValueError:
                continue

        return None

    def calcular_duracion_horas(self, hora_inicio: str, hora_fin: str) -> float:
        inicio_min = self._parse_hora_a_minutos(hora_inicio)
        fin_min = self._parse_hora_a_minutos(hora_fin)

        if inicio_min is None or fin_min is None:
            return 0.0

        if fin_min < inicio_min:
            fin_min += 24 * 60

        return round((fin_min - inicio_min) / 60, 2)

    def extraer_cod_curso(self, curso: str) -> str:
        if not curso:
            return ""
        return str(curso).strip()[:4].upper()

    def extraer_cod_modalidad(self, modalidad: str) -> str:
        modalidad_norm = str(modalidad or "").strip().upper()

        if modalidad_norm.startswith("PRE"):
            return "PRE"
        if modalidad_norm.startswith("VIR"):
            return "VIR"

        return modalidad_norm[:3]

    def construir_cod_mod(self, curso: str, modalidad: str) -> str:
        return f"{self.extraer_cod_curso(curso)}{self.extraer_cod_modalidad(modalidad)}"

    def _normalizar_valor(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip().upper()

    def _to_float(self, value) -> float:
        if value is None or value == "":
            return 0.0
        try:
            return float(str(value).replace(",", ".").strip())
        except Exception:
            return 0.0

    # =========================
    # DASHBOARD
    # =========================

    async def construir_dashboard(self, dni: str) -> dict:
        await self._cargar_cache_maestro()

        tutor = self._cache["tutores_by_dni"].get(str(dni).strip())
        if not tutor:
            return {"tutor": None, "resumen": {}, "detalle": []}

        tipo_tutor = self._normalizar_valor(tutor["TipoTutor"])
        precio_map = (
            self._cache["precio_antiguo_map"]
            if tipo_tutor == "ANTIGUO"
            else self._cache["precio_nuevo_map"]
        )

        reportes = await self.obtener_todos_los_reportes()

        detalle = []
        total_horas = 0.0
        total_estimado = 0.0
        total_reportes = 0
        total_virtuales = 0
        total_presenciales = 0

        for reporte in reportes:
            if reporte["DNI"] != str(dni).strip():
                continue

            total_reportes += 1

            modalidad = str(reporte.get("Modalidad", "")).strip().upper()
            if modalidad == "VIRTUAL":
                total_virtuales += 1
            elif modalidad == "PRESENCIAL":
                total_presenciales += 1

            duracion_horas = self.calcular_duracion_horas(
                reporte.get("HoraInicio"),
                reporte.get("HoraFin")
            )
            total_horas += duracion_horas

            cod_curso = self.extraer_cod_curso(reporte.get("Curso"))
            cod_modalidad = self.extraer_cod_modalidad(reporte.get("Modalidad"))
            cod_mod = self.construir_cod_mod(reporte.get("Curso"), reporte.get("Modalidad"))
            cod_idioma = self._cache["dim_idioma_map"].get(self._normalizar_valor(cod_mod), "")
            precio = precio_map.get(self._normalizar_valor(cod_idioma), 0.0)

            monto_estimado = round(duracion_horas * precio, 2)
            total_estimado += monto_estimado

            detalle.append({
                "FechaReporte": reporte.get("FechaReporte"),
                "NombreAlumno": reporte.get("NombreAlumno"),
                "Curso": reporte.get("Curso"),
                "Modalidad": reporte.get("Modalidad"),
                "HoraInicio": reporte.get("HoraInicio"),
                "HoraFin": reporte.get("HoraFin"),
                "DuracionHoras": duracion_horas,
                "CodCurso": cod_curso,
                "CodModalidad": cod_modalidad,
                "CodMod": cod_mod,
                "CodIdioma": cod_idioma,
                "Precio": precio,
                "MontoEstimado": monto_estimado,
                "TipoReporte": reporte.get("TipoReporte"),
                "TemasRealizados": reporte.get("TemasRealizados"),
                "TareasRealizadas": reporte.get("TareasRealizadas"),
                "ActitudEstudiante": reporte.get("ActitudEstudiante"),
                "LogrosEstudiante": reporte.get("LogrosEstudiante"),
                "Recomendacion": reporte.get("Recomendacion"),
            })

        nombre = str(tutor.get("Nombres", "")).strip()
        ap_paterno = str(tutor.get("ApellidoPaterno", "")).strip()
        ap_materno = str(tutor.get("ApellidoMaterno", "")).strip()

        nombre_completo = f"{ap_paterno} {ap_materno} {nombre}".strip()

        tutor_out = {
            "dni": tutor["DNI"],
            "codigo": tutor["Codigo"],
            "nombre": tutor["NombreID"],
            "nombreCompleto": nombre_completo,
            "tipoTutor": tutor["TipoTutor"],
            "activo": tutor["Activo"],
}

        resumen = {
            "totalReportes": total_reportes,
            "totalHoras": round(total_horas, 2),
            "totalVirtuales": total_virtuales,
            "totalPresenciales": total_presenciales,
            "estimadoTotal": round(total_estimado, 2),
        }

        def parse_fecha(fecha):
            if not fecha:
                return datetime.min
            try:
                return datetime.fromisoformat(str(fecha).replace("Z", ""))
            except Exception:
                return datetime.min

        detalle.sort(key=lambda x: parse_fecha(x.get("FechaReporte")))

        return {
            "tutor": tutor_out,
            "resumen": resumen,
            "detalle": detalle,
        }
