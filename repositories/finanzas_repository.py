from database.firebase_config import db
import datetime

class FinanzasRepository:
    @staticmethod
    def registrar_gasto(concepto, monto, metodo_pago, responsable):
        db.collection("gastos_diarios").add({
            "concepto": concepto, "monto": float(monto), "metodo_pago": metodo_pago, 
            "responsable": responsable, "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
        })

    @staticmethod
    def obtener_resumen_financiero_hoy():
        hoy = datetime.datetime.now(datetime.timezone.utc).date()
        ingresos, gastos = 0.0, 0.0
        
        for doc in db.collection("admisiones_diarias").stream():
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
        
        for doc in db.collection("admisiones_diarias").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy and datos.get("metodo_pago") != "Cortesía":
                movimientos.append({
                    "hora": f.strftime("%H:%M") if hasattr(f, 'strftime') else str(f)[11:16],
                    "tipo": "INGRESO", "categoria": datos.get("especialidad", "Ingreso General"),
                    "descripcion": f"Paciente: {datos.get('nombre_paciente', 'Desconocido')}",
                    "monto": float(datos.get("monto", 0) or 0), "metodo": datos.get("metodo_pago", "Efectivo")
                })
                
        for doc in db.collection("gastos_diarios").stream():
            datos = doc.to_dict() or {}
            f = datos.get("fecha_registro")
            es_hoy = (f.date() == hoy) if hasattr(f, 'date') else (isinstance(f, str) and str(hoy) in f)
            if es_hoy:
                movimientos.append({
                    "hora": f.strftime("%H:%M") if hasattr(f, 'strftime') else str(f)[11:16],
                    "tipo": "EGRESO", "categoria": "Gasto Administrativo",
                    "descripcion": datos.get("concepto", "Sin detalle"),
                    "monto": float(datos.get("monto", 0) or 0), "metodo": datos.get("metodo_pago", "Efectivo")
                })
                
        movimientos.sort(key=lambda x: x.get('hora', '00:00'))
        return movimientos