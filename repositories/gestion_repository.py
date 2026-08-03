from database.firebase_config import db
import datetime
import hashlib

class GestionRepository:
    @staticmethod
    def obtener_todos_los_usuarios():
        return [{"username": doc.id, **(doc.to_dict() or {})} for doc in db.collection("usuarios").stream()]

    @staticmethod
    def guardar_usuario(username, nombres, apellidos, rol, pwd_plano=None, estado="ACTIVO"):
        datos = {"nombres": nombres, "apellidos": apellidos, "rol": rol.upper(), "estado": estado.upper()}
        if pwd_plano and str(pwd_plano).strip():
            datos["pwd"] = hashlib.sha256(str(pwd_plano).strip().encode()).hexdigest()
        db.collection("usuarios").document(username).set(datos, merge=True)

    @staticmethod
    def registrar_admision(dni, nombre_paciente, especialidad, monto, metodo_pago, autoriza_cortesia=""):
        db.collection("admisiones_diarias").add({
            "dni": dni, "nombre_paciente": nombre_paciente, "especialidad": especialidad,
            "monto": float(monto), "metodo_pago": metodo_pago, "autoriza_cortesia": autoriza_cortesia,
            "estado": "Pendiente de Triaje", "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
        })

    @staticmethod
    def obtener_cola_triaje():
        registros = [{"id_admision": doc.id, **doc.to_dict()} for doc in db.collection("admisiones_diarias").where("estado", "==", "Pendiente de Triaje").stream()]
        registros.sort(key=lambda x: x.get('fecha_registro', datetime.datetime.max))
        return registros

    @staticmethod
    def actualizar_estado_admision(id_admision, nuevo_estado):
        db.collection("admisiones_diarias").document(id_admision).update({"estado": nuevo_estado})

    @staticmethod
    def obtener_cola_consultorio():
        registros = [{"id_admision": doc.id, **doc.to_dict()} for doc in db.collection("admisiones_diarias").where("estado", "==", "Listo para Consultorio").stream()]
        registros.sort(key=lambda x: x.get('fecha_registro', datetime.datetime.max))
        return registros