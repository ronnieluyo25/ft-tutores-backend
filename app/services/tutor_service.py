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

    # 🔽 ORDENAR POR FECHA (ASCENDENTE)
    def parse_fecha(fecha):
        if not fecha:
            return datetime.min
        try:
            return datetime.fromisoformat(fecha.replace("Z", ""))
        except Exception:
            return datetime.min

    detalle.sort(key=lambda x: parse_fecha(x.get("FechaReporte")))

    # =========================
    # DATOS TUTOR
    # =========================

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

    # =========================
    # RESUMEN
    # =========================

    resumen = {
        "totalReportes": total_reportes,
        "totalHoras": round(total_horas, 2),
        "totalVirtuales": total_virtuales,
        "totalPresenciales": total_presenciales,
        "estimadoTotal": round(total_estimado, 2),
    }

    return {
        "tutor": tutor_out,
        "resumen": resumen,
        "detalle": detalle,
    }