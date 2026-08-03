from database.firebase_config import db
import datetime

class FarmaciaRepository:
    @staticmethod
    def buscar_tickets_farmacia(query_text=""):
        q = str(query_text).strip().lower()
        if not q: docs = db.collection("cola_farmacia").where("estado", "==", "Pendiente").stream()
        else: docs = db.collection("cola_farmacia").limit(100).stream()

        res = []
        for d in docs:
            dat = {"id_ticket": d.id, **d.to_dict()}
            if not q or (q in dat.get("dni", "").lower() or q in dat.get("nombre_paciente", "").lower()): res.append(dat)
        res.sort(key=lambda x: x.get('fecha_registro', datetime.datetime.min), reverse=True)
        return res

    @staticmethod
    def obtener_inventario_producto(nombre_producto):
        nom_limpio = str(nombre_producto).replace("/", "_").strip()
        doc = db.collection("inventario_farmacia").document(nom_limpio).get()
        if doc.exists: return doc.to_dict()
        return {"stock": 0, "precio": 0.0, "stock_minimo": 10, "lote": "-", "fecha_vencimiento": "-"}

    @staticmethod
    def actualizar_inventario_producto(nombre_producto, stock_adicional, nuevo_precio, stock_minimo, lote, fecha_venc):
        nom_limpio = str(nombre_producto).replace("/", "_").strip()
        ref = db.collection("inventario_farmacia").document(nom_limpio)
        doc = ref.get()
        datos_nuevos = {"precio": float(nuevo_precio), "stock_minimo": int(stock_minimo), "lote": str(lote).strip().upper(), "fecha_vencimiento": str(fecha_venc).strip()}
        if doc.exists:
            datos_nuevos["stock"] = doc.to_dict().get("stock", 0) + int(stock_adicional)
            ref.update(datos_nuevos)
        else:
            datos_nuevos["stock"] = int(stock_adicional)
            ref.set(datos_nuevos)

    @staticmethod
    def procesar_venta_farmacia(dni, nombre, monto, metodo_pago, items_vendidos, id_ticket=None, estado_decision="Vendido"):
        if estado_decision == "Vendido":
            for item in items_vendidos:
                nom_limpio = str(item.get("medicamento", "")).replace("/", "_").strip()
                cant = int(item.get("cantidad", 0))
                if nom_limpio and cant > 0:
                    ref = db.collection("inventario_farmacia").document(nom_limpio)
                    doc = ref.get()
                    if doc.exists:
                        ref.update({"stock": doc.to_dict().get("stock", 0) - cant})
                    else:
                        ref.set({"stock": -cant, "precio": 0.0, "stock_minimo": 10, "lote": "SIN REGISTRO", "fecha_vencimiento": "N/A"})
        
        if id_ticket: db.collection("cola_farmacia").document(id_ticket).update({"estado": estado_decision})
        
        if estado_decision == "Vendido" and float(monto) > 0:
            db.collection("admisiones_diarias").add({
                "dni": dni, "nombre_paciente": nombre, "especialidad": "Venta de Farmacia",
                "monto": float(monto), "metodo_pago": metodo_pago, "autoriza_cortesia": "",
                "estado": "Completado", "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
            })

    @staticmethod
    def obtener_alertas_inventario():
        alertas = []
        for doc in db.collection("inventario_farmacia").stream():
            datos = {"medicamento": str(doc.id).replace("_", "/"), **doc.to_dict()}
            if int(datos.get("stock", 0)) <= int(datos.get("stock_minimo", 10)): alertas.append(datos)
        return alertas