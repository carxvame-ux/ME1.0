from database.firebase_config import db
import datetime

class FinanzasRepository:
    @staticmethod
    def registrar_gasto(concepto, monto, metodo_pago, responsable):
        db.collection("gastos_diarios").add({
            "concepto": concepto, "monto": float(monto), "metodo_pago": metodo_pago, 
            "responsable": responsable, "fecha_registro": datetime.datetime.now(datetime.timezone.utc),
            "estado_caja": "Abierto"
        })

    @staticmethod
    def cerrar_turno(ingresos, gastos, movimientos, responsable):
        id_turno = f"TURNO-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        for m in movimientos:
            if "id" in m:
                if m["tipo"] == "INGRESO":
                    db.collection("admisiones_diarias").document(m["id"]).update({"estado_caja": "Cerrado", "id_turno": id_turno})
                elif m["tipo"] == "EGRESO":
                    db.collection("gastos_diarios").document(m["id"]).update({"estado_caja": "Cerrado", "id_turno": id_turno})

        db.collection("cierres_caja").add({
            "id_turno": id_turno,
            "fecha_cierre": datetime.datetime.now(datetime.timezone.utc),
            "ingresos_totales": ingresos,
            "gastos_totales": gastos,
            "saldo_neto": ingresos - gastos,
            "responsable": responsable
        })

        return id_turno

    @staticmethod
    def obtener_resumen_financiero_hoy():
        hoy = datetime.datetime.now(datetime.timezone.utc).date()
        ingresos, gastos = 0.0, 0.0
        
        for doc in db.collection("admisiones_diarias").where("estado_caja", "==", "Abierto").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy and datos.get("metodo_pago") != "Cortesía": ingresos += float(datos.get("monto", 0) or 0)
            
        for doc in db.collection("gastos_diarios").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy: gastos += float(datos.get("monto", 0) or 0)
            
        return {"ingresos": ingresos, "gastos": gastos, "saldo": ingresos - gastos}

    @staticmethod
    def obtener_detalles_financieros_hoy():
        hoy = datetime.datetime.now(datetime.timezone.utc).date()
        movimientos = []
        
        for doc in db.collection("admisiones_diarias").where("estado_caja", "==", "Abierto").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy and datos.get("metodo_pago") != "Cortesía":
                movimientos.append({
                    "id": doc.id,
                    "hora": f.strftime("%H:%M") if hasattr(f, 'strftime') else str(f)[11:16],
                    "tipo": "INGRESO", "categoria": datos.get("especialidad", "Ingreso General"),
                    "descripcion": f"Paciente: {datos.get('nombre_paciente', 'Desconocido')}",
                    "monto": float(datos.get("monto", 0) or 0), "metodo": datos.get("metodo_pago", "Efectivo")
                })
                
        for doc in db.collection("gastos_diarios").where("estado_caja", "==", "Abierto").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy:
                movimientos.append({
                    "id": doc.id,
                    "hora": f.strftime("%H:%M") if hasattr(f, 'strftime') else str(f)[11:16],
                    "tipo": "EGRESO", "categoria": "Gasto Administrativo",
                    "descripcion": datos.get("concepto", "Sin detalle"),
                    "monto": float(datos.get("monto", 0) or 0), "metodo": datos.get("metodo_pago", "Efectivo")
                })
                
        movimientos.sort(key=lambda x: x.get('hora', '00:00'))
        return movimientos