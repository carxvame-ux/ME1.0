import firebase_admin
from firebase_admin import credentials, firestore
import datetime

print("Iniciando conexión con Firebase...")

try:
    # 1. Inicializar la conexión limpia (leerá el proyecto nuevo de tu JSON)
    cred = credentials.Certificate('credenciales.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("¡Conexión exitosa!")
except Exception as e:
    print(f"Error al conectar: {e}")
    exit()

ahora = datetime.datetime.now(datetime.timezone.utc)

datos_iniciales = {
    "usuarios": {
        "doc_id": "usuario_admin_01",
        "data": {
            "nombres": "Carlos",
            "apellidos": "Vasquez",
            "rol": "ADMINISTRADOR",
            "estado": "ACTIVO"
        }
    },
    "pacientes": {
        "doc_id": "12345678",
        "data": {
            "dni": "12345678",
            "nombres": "Juan Carlos",
            "apellidos": "Pérez Gómez",
            "fecha_registro": ahora
        }
    },
    "citas": {
        "doc_id": "cita_prueba_001",
        "data": {
            "paciente_id": "12345678",
            "estado": "PENDIENTE"
        }
    },
    "historias_clinicas": {
        "doc_id": "historia_prueba_001",
        "data": {
            "paciente_id": "12345678",
            "diagnostico_principal": "Paciente sano"
        }
    },
    "inventario": {
        "doc_id": "prod_paracetamol_01",
        "data": {
            "nombre_comercial": "Panadol Antigripal",
            "stock_actual": 50
        }
    },
    "finanzas": {
        "doc_id": "transaccion_prueba_001",
        "data": {
            "tipo": "INGRESO",
            "monto": 80.00
        }
    }
}

print("Creando colecciones...")

for coleccion, info in datos_iniciales.items():
    try:
        doc_ref = db.collection(coleccion).document(info["doc_id"])
        doc_ref.set(info["data"])
        print(f"✅ Colección '{coleccion}' lista.")
    except Exception as e:
        print(f"❌ Error al crear '{coleccion}': {e}")

print("\n🚀 ¡Base de datos inicializada con éxito!")