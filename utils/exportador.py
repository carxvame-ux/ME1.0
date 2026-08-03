import csv
import os
from datetime import datetime
from repositories.pacientes_repository import PacientesRepository

def generar_reporte_excel():
    print("Iniciando extracción de datos de Firestore...")
    pacientes = PacientesRepository.obtener_todos()
    
    if not pacientes:
        print("No hay pacientes para exportar.")
        return None
        
    # Nombre del archivo con marca de tiempo exacta para no sobreescribir reportes anteriores
    fecha_hoy = datetime.now().strftime("%d_%m_%Y_%H%M")
    nombre_archivo = f"Reporte_Pacientes_{fecha_hoy}.csv"
    ruta_guardado = os.path.join(os.getcwd(), nombre_archivo)
    
    try:
        # utf-8-sig fuerza a Excel a respetar el idioma español (BOM)
        with open(ruta_guardado, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file, delimiter=';') # Punto y coma es el estándar de Excel aquí
            
            # 1. Cabecera Gerencial del Documento
            writer.writerow(["REPORTE GENERAL DE PACIENTES - CONSULTORIO MÉDICO"])
            writer.writerow(["Dr. Jesús García Mendoza"])
            writer.writerow(["Generado el:", datetime.now().strftime("%d/%m/%Y %I:%M %p")])
            writer.writerow([]) # Fila vacía para separar
            
            # 2. Títulos de las Columnas
            writer.writerow(["DNI", "NOMBRES", "APELLIDOS", "TELÉFONO", "FECHA DE INGRESO AL SISTEMA"])
            
            # 3. Llenado de Datos desde Firebase
            for p in pacientes:
                f_obj = p.get('fecha_registro')
                # Verificamos si la fecha existe y la formateamos a DD/MM/YYYY
                f_str = f_obj.strftime("%d/%m/%Y") if f_obj else "Sin registro"
                
                writer.writerow([
                    p.get('dni', 'N/A'),
                    p.get('nombres', 'N/A'),
                    p.get('apellidos', 'N/A'),
                    p.get('telefono', 'Sin número'),
                    f_str
                ])
                
        print(f"Reporte generado con éxito en: {ruta_guardado}")
        return ruta_guardado
        
    except Exception as e:
        print(f"Error crítico al generar Excel: {e}")
        return "ERROR"