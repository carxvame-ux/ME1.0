import csv
import os

def cargar_catalogo_local():
    medicamentos = []
    # Usamos la ruta directa absoluta basada en desde donde ejecutas el programa
    ruta_base = os.getcwd()
    ruta_csv = os.path.join(ruta_base, "catalogoproductos.xlsx - Catálogo.csv")
    
    if not os.path.exists(ruta_csv):
        print(f"⚠️ ATENCIÓN: No se encontró el archivo en: {ruta_csv}")
        return ["Archivo no encontrado"]
        
    try:
        # errors='ignore' fue la clave mágica para evitar que caracteres raros rompan la lectura
        with open(ruta_csv, mode='r', encoding='utf-8-sig', errors='ignore') as file:
            texto_muestra = file.read(2048)
            delimitador = ';' if ';' in texto_muestra else ','
            file.seek(0)
            
            reader = csv.DictReader(file, delimiter=delimitador)
            
            for row in reader:
                nom = row.get('Nom_Prod', '').strip()
                conc = row.get('Concent', '').strip()
                forma = row.get('Nom_Form_Farm', '').strip()
                
                if nom:
                    # Unimos el nombre, la dosis y la presentación
                    nombre_completo = f"{nom} {conc} {forma}".strip()
                    medicamentos.append(nombre_completo)
                    
        lista_final = sorted(list(set(medicamentos)))
        print(f"✅ ¡Éxito! Catálogo cargado en memoria RAM: {len(lista_final)} medicamentos listos para buscar.")
        return lista_final
        
    except Exception as e:
        print(f"❌ Error al procesar el catálogo: {e}")
        return []

# Almacenamos la base de datos en RAM
CATALOGO_MEDICAMENTOS = cargar_catalogo_local()