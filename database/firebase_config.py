import firebase_admin
from firebase_admin import credentials, firestore

# Aplicamos el Patrón Singleton para garantizar una única conexión
def obtener_conexion():
    if not firebase_admin._apps:
        # Apunta al archivo en la raíz del proyecto
        cred = credentials.Certificate('credenciales.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Instancia global exportable
db = obtener_conexion()