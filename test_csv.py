import csv
import os

def diagnosticar_archivo():
    ruta = "catalogoproductos.xlsx - Catálogo.csv"
    print("\n" + "="*50)
    print(f"🔍 INICIANDO DIAGNÓSTICO DE DATOS")
    print("="*50)
    print(f"📂 Buscando archivo en:\n{os.path.abspath(ruta)}\n")

    if not os.path.exists(ruta):
        print("❌ ERROR CRÍTICO: Python no encuentra el archivo.")
        print("Asegúrate de que esté en la carpeta D:\\MEDICOS y que el nombre sea exactamente ese.")
        return

    try:
        with open(ruta, mode='r', encoding='utf-8-sig', errors='ignore') as f:
            texto_muestra = f.read(2000)
            delimitador = ';' if ';' in texto_muestra else ','
            print(f"✅ Archivo encontrado.")
            print(f"✅ Delimitador detectado: '{delimitador}'\n")
            
            f.seek(0)
            lector = csv.DictReader(f, delimiter=delimitador)
            columnas = lector.fieldnames
            
            print("📌 COLUMNAS EXACTAS QUE VE PYTHON:")
            for col in columnas:
                print(f"  - '{col}'")
            
            filas = list(lector)
            print(f"\n💊 Total de medicamentos detectados en el archivo: {len(filas)}")
            
            if len(filas) > 0:
                print("\n📄 Ejemplo de la primera fila leída:")
                print(filas[0])
                
    except Exception as e:
        print(f"❌ Ocurrió un error al intentar leer el archivo: {e}")

if __name__ == "__main__":
    diagnosticar_archivo()