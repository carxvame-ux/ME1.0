from fpdf import FPDF
import os
import re

def limpiar_texto(texto):
    if not texto or str(texto).strip() == "": 
        return " "
    texto = str(texto).strip()
    reemplazos = {
        "ñ":"n", "Ñ":"N", 
        "á":"a", "é":"e", "í":"i", "ó":"o", "ú":"u", 
        "Á":"A", "É":"E", "Í":"I", "Ó":"O", "Ú":"U",
        "\t": " ", "\n": " " 
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

class RecetaMedicaPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(21, 101, 192) 
        self.set_x(10)
        self.cell(190, 10, 'SISTEMA DE CONSULTORIO MEDICO', border=False, ln=True, align='C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.set_x(10)
        self.cell(190, 5, 'Dr. Jesus Garcia Mendoza - CMP: 12345', border=False, ln=True, align='C')
        self.set_x(10)
        self.cell(190, 5, 'Tumbes, Peru', border=False, ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.set_x(10)
        self.cell(190, 10, f'Pagina {self.page_no()}', align='C')

def crear_pdf_receta(nombre_paciente, dni_paciente, fecha, motivo, diagnostico, medicamentos, instrucciones):
    pdf = RecetaMedicaPDF()
    pdf.add_page()

    nombre_paciente = limpiar_texto(nombre_paciente)
    fecha = limpiar_texto(fecha)
    motivo = limpiar_texto(motivo)
    diagnostico = limpiar_texto(diagnostico)
    instrucciones = limpiar_texto(instrucciones)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(10)
    pdf.cell(190, 8, f"Paciente: {nombre_paciente}", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_x(10)
    pdf.cell(190, 8, f"DNI: {dni_paciente}      Fecha de Atencion: {fecha}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_x(10)
    pdf.cell(190, 8, "Motivo de Consulta:", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_x(10)
    pdf.multi_cell(190, 6, motivo)
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_x(10)
    pdf.cell(190, 8, "Diagnostico:", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_x(10)
    pdf.multi_cell(190, 6, diagnostico)
    pdf.ln(8)

    pdf.set_fill_color(240, 248, 255) 
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(21, 101, 192)
    pdf.set_x(10)
    pdf.cell(190, 8, " RECETA MEDICA E INDICACIONES", border=1, ln=True, fill=True)
    pdf.ln(3)

    for i, med in enumerate(medicamentos, 1):
        med_nom = limpiar_texto(med.get('nombre', ''))
        med_dos = limpiar_texto(med.get('dosis', ''))
        med_frec = limpiar_texto(med.get('frecuencia', ''))
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_x(10) 
        pdf.multi_cell(190, 6, f"{i}. {med_nom}") 
        
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(80, 80, 80)
        texto_dosis = f"      Tomar: {med_dos}   |   Frecuencia: {med_frec}"
        pdf.set_x(10) 
        pdf.multi_cell(190, 6, texto_dosis)
        pdf.ln(2)
        
        pdf.set_draw_color(220, 220, 220)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.set_draw_color(0, 0, 0) 
        pdf.ln(3)

    pdf.ln(5)

    if instrucciones and instrucciones != " ":
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_x(10)
        pdf.cell(190, 8, "Instrucciones Medicas Generales:", ln=True)
        pdf.set_font("helvetica", "", 11)
        pdf.set_x(10)
        pdf.multi_cell(190, 6, instrucciones)

    nombre_limpio = nombre_paciente.replace(" ", "_")
    fecha_segura = re.sub(r'[^a-zA-Z0-9]', '_', fecha)
    nombre_archivo = f"Receta_{nombre_limpio}_{fecha_segura}.pdf"
    ruta_guardado = os.path.join(os.getcwd(), nombre_archivo)
    
    pdf.output(ruta_guardado)
    return ruta_guardado

def enviar_a_impresora(ruta_pdf):
    try:
        ruta_absoluta = os.path.abspath(ruta_pdf)
        os.startfile(ruta_absoluta, "print")
        return True, "Impresora Predeterminada"
    except Exception as e:
        print(f"Error nativo de impresión: {e}")
        return False, str(e)