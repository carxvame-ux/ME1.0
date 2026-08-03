from database.firebase_config import db
import datetime

class AgendaRepository:
    @staticmethod
    def registrar_cita(dni_paciente, nombre_paciente, id_medico, nombre_medico, fecha_str, hora_str, motivo=""):
        # fecha_str debe ser formato YYYY-MM-DD
        db.collection("citas").add({
            "dni_paciente": dni_paciente,
            "nombre_paciente": nombre_paciente,
            "id_medico": id_medico,
            "nombre_medico": nombre_medico,
            "fecha": fecha_str,
            "hora": hora_str,
            "motivo": motivo,
            "estado": "Pendiente",
            "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
        })

    @staticmethod
    def obtener_citas_por_fecha(fecha_str):
        registros = [{"id": doc.id, **doc.to_dict()} for doc in db.collection("citas").where("fecha", "==", fecha_str).stream()]
        registros.sort(key=lambda x: x.get('hora', '00:00'))
        return registros

    @staticmethod
    def actualizar_estado_cita(id_cita, nuevo_estado):
        db.collection("citas").document(id_cita).update({"estado": nuevo_estado})
