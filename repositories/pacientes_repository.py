from database.firebase_config import db
import datetime

class PacientesRepository:
    @staticmethod
    def _generar_terminos_busqueda(nombres, apellidos):
        terminos = set()
        texto_completo = f"{nombres} {apellidos}".lower()
        for palabra in texto_completo.split():
            for i in range(1, len(palabra) + 1): terminos.add(palabra[:i])
        terminos.add(str(apellidos).lower())
        return list(terminos)

    @staticmethod
    def registrar_paciente(dni, nombres, apellidos, telefono):
        terminos = PacientesRepository._generar_terminos_busqueda(nombres, apellidos)
        db.collection("pacientes").document(dni).set({
            "dni": dni, "nombres": nombres, "apellidos": apellidos, "telefono": telefono,
            "apellidos_lower": str(apellidos).lower(), "terminos_busqueda": terminos, 
            "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
        }, merge=True)

    @staticmethod
    def buscar_paciente_mixto(query_text):
        query_text = str(query_text).strip()
        if query_text.isdigit():
            doc = db.collection("pacientes").document(query_text).get()
            return [doc.to_dict()] if doc.exists else []
        query_lower = query_text.lower() 
        nuevos = [doc.to_dict() for doc in db.collection("pacientes").where("terminos_busqueda", "array_contains", query_lower).limit(20).stream()]
        antiguos = [doc.to_dict() for doc in db.collection("pacientes").where("apellidos_lower", ">=", query_lower).where("apellidos_lower", "<=", query_lower + "\uf8ff").limit(20).stream()]
        return list({doc['dni']: doc for doc in (nuevos + antiguos)}.values())

    @staticmethod
    def obtener_por_dni(dni):
        doc = db.collection("pacientes").document(dni).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def guardar_signos_vitales(dni, peso, talla, imc, fc="", fr="", pa="", temp="", sat=""):
        db.collection("pacientes").document(dni).collection("signos_vitales").add({
            "peso": peso, "talla": talla, "imc": imc, "fc": fc, "fr": fr, "pa": pa, "temp": temp, "sat": sat,
            "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
        })

    @staticmethod
    def obtener_historial_signos(dni):
        registros = [doc.to_dict() for doc in db.collection("pacientes").document(dni).collection("signos_vitales").stream()]
        registros.sort(key=lambda x: x.get('fecha_registro', datetime.datetime.min), reverse=True)
        return registros

    @staticmethod
    def guardar_historia_dinamica(dni, datos_historia):
        datos_historia["fecha_registro"] = datetime.datetime.now(datetime.timezone.utc)
        db.collection("pacientes").document(dni).collection("historias_clinicas").add(datos_historia)
        receta = datos_historia.get("receta", [])
        if receta:
            try:
                pac = PacientesRepository.obtener_por_dni(dni) or {}
                db.collection("cola_farmacia").add({
                    "dni": dni, "nombre_paciente": f"{pac.get('nombres','')} {pac.get('apellidos','')}", 
                    "receta": receta, "estado": "Pendiente", "medico": datos_historia.get("medico_tratante", "Médico"),
                    "fecha_registro": datetime.datetime.now(datetime.timezone.utc)
                })
            except: pass

    @staticmethod
    def obtener_historias_dinamicas(dni):
        registros = [doc.to_dict() for doc in db.collection("pacientes").document(dni).collection("historias_clinicas").stream()]
        registros.sort(key=lambda x: x.get('fecha_registro', datetime.datetime.min), reverse=True)
        return registros