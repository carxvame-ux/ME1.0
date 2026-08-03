import flet as ft
import traceback
import pandas as pd
import os
import datetime
import webbrowser

# ==========================================
# 🚀 MOTOR EN MEMORIA RAM (Carga Global)
# ==========================================
_CATALOGO_MEMORIA = []

def _cargar_catalogo_en_memoria():
    global _CATALOGO_MEMORIA
    if _CATALOGO_MEMORIA: return 
    
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nombres_archivo = ["catalogoproductos.xlsx - Catálogo.csv", "catalogoproductos.csv", "assets/data/catalogoproductos.csv"]
    
    df_meds = None
    for nombre in nombres_archivo:
        ruta_completa = os.path.join(ruta_base, nombre)
        if os.path.exists(ruta_completa):
            try:
                df_meds = pd.read_csv(ruta_completa, sep=";", encoding="utf-8")
            except UnicodeDecodeError:
                try: df_meds = pd.read_csv(ruta_completa, sep=";", encoding="latin-1")
                except: continue
            except: continue
            
            if df_meds is not None and "Nom_Prod" in df_meds.columns: break 

    if df_meds is not None and "Nom_Prod" in df_meds.columns:
        df_meds["Nom_Prod"] = df_meds["Nom_Prod"].fillna("").astype(str).str.strip()
        df_meds["Concent"] = df_meds["Concent"].fillna("").astype(str).str.strip()
        df_meds["Nom_Form_Farm"] = df_meds["Nom_Form_Farm"].fillna("").astype(str).str.strip()
        _CATALOGO_MEMORIA = (df_meds["Nom_Prod"] + " " + df_meds["Concent"] + " - " + df_meds["Nom_Form_Farm"]).unique().tolist()
    else:
        _CATALOGO_MEMORIA = ["PARACETAMOL 500 mg - Tableta", "IBUPROFENO 400 mg - Tableta", "OMEPRAZOL 20 mg - Cápsula"]

_cargar_catalogo_en_memoria()


def obtener_historia_clinica_view(page: ft.Page, dni_seleccionado="", on_back=None, on_navigate=None, dni="", **kwargs):
    try:
        from repositories.pacientes_repository import PacientesRepository
        
        dni_final = dni_seleccionado if dni_seleccionado else dni
        usuario = getattr(page, "usuario_actual", None)
        nombre_medico = usuario["nombre"] if usuario else "Médico Tratante"

        paciente = PacientesRepository.obtener_por_dni(dni_final) or {}
        nombres_completos = f"{paciente.get('nombres', '')} {paciente.get('apellidos', '')}"
        
        signos_previos = PacientesRepository.obtener_historial_signos(dni_final)
        ultimo_peso = str(signos_previos[0].get("peso", "")) if signos_previos else ""
        ultima_fc = str(signos_previos[0].get("fc", "")) if signos_previos else ""
        ultima_fr = str(signos_previos[0].get("fr", "")) if signos_previos else ""
        ultima_pa = str(signos_previos[0].get("pa", "")) if signos_previos else ""
        ultima_temp = str(signos_previos[0].get("temp", "")) if signos_previos else ""
        ultima_sat = str(signos_previos[0].get("sat", "")) if signos_previos else ""

        def volver(e=None):
            if on_back: on_back()
            elif on_navigate: on_navigate("/") 

        barra_superior = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Volver", icon_color="white", on_click=volver),
            title=ft.Text(f"Consultorio | Dr. {nombre_medico} | Paciente: {nombres_completos}", color="white", size=16, weight="bold"),
            bgcolor=ft.Colors.BLUE_900
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass

        # ==========================================
        # GESTIÓN DE ARCHIVOS ADJUNTOS
        # ==========================================
        import shutil
        TEMP_UPLOAD_DIR = os.path.join(os.getcwd(), "temp_uploads")
        if not os.path.exists(TEMP_UPLOAD_DIR):
            os.makedirs(TEMP_UPLOAD_DIR)

        archivos_adjuntos = []
        lista_archivos_ui = ft.ListView(height=100, spacing=5)

        def on_dialog_result(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    try:
                        dest_path = os.path.join(TEMP_UPLOAD_DIR, f.name)
                        shutil.copy2(f.path, dest_path)
                        archivos_adjuntos.append({"nombre": f.name, "ruta": dest_path})
                        lista_archivos_ui.controls.append(
                            ft.ListTile(leading=ft.Icon(ft.Icons.ATTACH_FILE), title=ft.Text(f.name))
                        )
                        mostrar_mensaje(f"Archivo {f.name} adjuntado.", ft.Colors.GREEN_700)
                    except Exception as ex:
                        mostrar_mensaje(f"Error al copiar archivo: {ex}", ft.Colors.RED_700)
                if page: page.update()

        file_picker = ft.FilePicker()
        file_picker.on_result = on_dialog_result
        page.overlay.append(file_picker)

        # ==========================================
        # VARIABLES DE FORMULARIO
        # ==========================================
        in_motivo = ft.TextField(label="Motivo de Consulta", multiline=True, min_lines=2, expand=True)
        in_tiempo_enf = ft.TextField(label="Tiempo de Enfermedad", width=200)
        dp_tipo_inicio = ft.Dropdown(label="Tipo de Inicio", options=[ft.dropdown.Option("Insidioso"), ft.dropdown.Option("Brusco")], width=150)
        
        in_apetito, in_sed, in_orina = ft.TextField(label="Apetito", width=180), ft.TextField(label="Sed", width=180), ft.TextField(label="Orina", width=180)
        in_deposiciones, in_sueno, in_peso_cambio = ft.TextField(label="Deposiciones", width=180), ft.TextField(label="Sueño", width=180), ft.TextField(label="Variación de Peso", width=180)

        in_cirugias, in_ram = ft.TextField(label="Cirugías Previas", expand=True), ft.TextField(label="RAM (Alergias)", expand=True)
        in_egd, in_colono = ft.TextField(label="EGD (Endoscopia)", expand=True), ft.TextField(label="Colonoscopia", expand=True)
        chk_hepatitis = ft.Checkbox(label="Hepatitis P.", value=False)
        
        chk_cafe, chk_gaseosa, chk_aji = ft.Checkbox(label="Café"), ft.Checkbox(label="Gaseosas"), ft.Checkbox(label="Ajíes")
        chk_ceviche, chk_alcohol, chk_tabaco = ft.Checkbox(label="Ceviches"), ft.Checkbox(label="Alcohol"), ft.Checkbox(label="Tabaco")

        in_fc, in_fr, in_pa = ft.TextField(label="F.C.", width=100, value=ultima_fc), ft.TextField(label="F.R.", width=100, value=ultima_fr), ft.TextField(label="P.A.", width=100, value=ultima_pa)
        in_temp, in_sat, in_peso_actual = ft.TextField(label="Temp.", width=100, value=ultima_temp), ft.TextField(label="SpO2.", width=100, value=ultima_sat), ft.TextField(label="Peso (kg)", width=100, value=ultimo_peso) 
        
        in_fisico = ft.TextField(label="Examen Físico Abdominal / Otros", multiline=True, min_lines=3, expand=True)
        in_dx1, in_dx2, in_dx3 = ft.TextField(label="Diagnóstico 1", expand=True), ft.TextField(label="Diagnóstico 2", expand=True), ft.TextField(label="Diagnóstico 3", expand=True)
        in_plan, in_cita = ft.TextField(label="Plan de Trabajo", multiline=True, min_lines=2, expand=True), ft.TextField(label="Próxima Cita", expand=True)

        # ==========================================
        # BUSCADOR INTELIGENTE EN MEMORIA RAM
        # ==========================================
        receta_actual = []
        lista_receta_ui = ft.ListView(height=180, spacing=5)

        in_med_nom = ft.TextField(label="Buscar medicamento (Ej: broncol, amoxi 500)...", expand=2)
        sugerencias_ui = ft.ListView(height=200, spacing=2)
        tarjeta_sugerencias = ft.Card(content=ft.Container(content=sugerencias_ui, padding=5), visible=False, elevation=4)

        def _seleccionar_med(med_nombre):
            in_med_nom.value = med_nombre
            tarjeta_sugerencias.visible = False
            if page: page.update()

        def limpiar_texto(texto):
            reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n', '-': ' '}
            txt = str(texto).lower().strip()
            for a, b in reemplazos.items(): txt = txt.replace(a, b)
            return txt

        def _filtrar_meds(e):
            texto_busqueda = in_med_nom.value.strip()
            sugerencias_ui.controls.clear()
            if len(texto_busqueda) > 1:
                palabras_clave = limpiar_texto(texto_busqueda).split()
                coincidencias = []
                for med in _CATALOGO_MEMORIA:
                    if all(palabra in limpiar_texto(med) for palabra in palabras_clave):
                        coincidencias.append(med)
                        if len(coincidencias) >= 15: break
                if coincidencias:
                    tarjeta_sugerencias.visible = True
                    for med in coincidencias:
                        sugerencias_ui.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.MEDICATION, color=ft.Colors.BLUE_700), title=ft.Text(med, size=13, weight="bold"), on_click=lambda ev, m=med: _seleccionar_med(m)))
                else: tarjeta_sugerencias.visible = False
            else: tarjeta_sugerencias.visible = False
            if page: page.update()

        in_med_nom.on_change = _filtrar_meds

        in_med_cant = ft.TextField(label="Cant.", width=80, keyboard_type="number")
        in_med_ind = ft.TextField(label="Indicación (Ej: 1 cada 8h)", expand=3)

        def agregar_med_receta(e):
            med_valor = in_med_nom.value.strip()
            if not med_valor or not in_med_cant.value: return

            # Verificación de stock en vivo
            from repositories.farmacia_repository import FarmaciaRepository
            datos_inv = FarmaciaRepository.obtener_inventario_producto(med_valor)
            stock_actual = datos_inv.get('stock', 0)

            try:
                cant_pedida = int(in_med_cant.value)
            except ValueError:
                cant_pedida = 1

            if stock_actual < cant_pedida:
                mostrar_mensaje(f"⚠️ Stock insuficiente en farmacia. Stock actual: {stock_actual}", ft.Colors.RED_700)
                # Opcional: Permitir agregar igual pero marcándolo visualmente, o bloquear.
                # Aquí lo bloquearemos para forzar una alternativa como se solicitó.
                return

            med = {"medicamento": med_valor, "cantidad": str(in_med_cant.value).strip(), "indicacion": str(in_med_ind.value).strip()}
            receta_actual.append(med)
            lista_receta_ui.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.ListTile(leading=ft.Icon(ft.Icons.VACCINES, color=ft.Colors.ORANGE_700), title=ft.Text(f"{med['cantidad']}x {med['medicamento']}", weight="bold"), subtitle=ft.Text(med['indicacion'])))))
            in_med_nom.value = in_med_cant.value = in_med_ind.value = ""
            tarjeta_sugerencias.visible = False
            if page: page.update()

        contenedor_buscador = ft.Column([
            ft.Row([in_med_nom, in_med_cant, in_med_ind, ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN_600, icon_size=40, tooltip="Agregar a receta", on_click=agregar_med_receta)], vertical_alignment=ft.CrossAxisAlignment.START),
            tarjeta_sugerencias
        ])

        # ==========================================
        # 🖨️ MOTOR DE IMPRESIÓN (GENERADOR PDF)
        # ==========================================
        def imprimir_receta(e):
            if not receta_actual:
                mostrar_mensaje("La receta está vacía. Agregue medicamentos primero.", ft.Colors.RED_700)
                return
            
            from utils.generador_pdf import crear_pdf_receta

            fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
            motivo_consulta = in_motivo.value or "Consulta General"
            diagnostico_txt = " - ".join(filter(None, [in_dx1.value, in_dx2.value, in_dx3.value])) or "En evaluación"
            
            # Adaptar los medicamentos al formato que espera el generador PDF
            meds_para_pdf = []
            for m in receta_actual:
                meds_para_pdf.append({
                    "nombre": m["medicamento"],
                    "dosis": str(m["cantidad"]),
                    "frecuencia": m["indicacion"]
                })
            
            instrucciones = in_plan.value or "Ninguna instrucción adicional."

            try:
                ruta_pdf = crear_pdf_receta(
                    nombre_paciente=nombres_completos,
                    dni_paciente=dni_final,
                    fecha=fecha_hoy,
                    motivo=motivo_consulta,
                    diagnostico=diagnostico_txt,
                    medicamentos=meds_para_pdf,
                    instrucciones=instrucciones
                )
                webbrowser.open(f"file:///{ruta_pdf.replace(chr(92), '/')}")
                mostrar_mensaje("Receta generada en PDF con éxito.", ft.Colors.GREEN_700)
            except Exception as ex:
                mostrar_mensaje(f"Error al generar PDF: {ex}", ft.Colors.RED_700)

        # ==========================================
        # HISTORIAL DEL PACIENTE
        # ==========================================
        lista_historial_ui = ft.ListView(expand=True, spacing=10)

        def cargar_historial_paciente():
            lista_historial_ui.controls.clear()
            historias = PacientesRepository.obtener_historias_dinamicas(dni_final)
            if not historias:
                lista_historial_ui.controls.append(ft.Text("Sin atenciones previas.", color=ft.Colors.GREY_500, italic=True))
            else:
                for h in historias:
                    f_raw = h.get('fecha_registro')
                    fecha_str = f_raw.strftime("%d/%m/%Y %H:%M") if hasattr(f_raw, 'strftime') else str(f_raw)[:16]
                    dxs = [dx for dx in h.get('diagnosticos', []) if dx]
                    str_dx = " | ".join(dxs) if dxs else "Sin dx."
                    recetas_pasadas = h.get('receta', [])
                    str_receta = "\n".join([f"- {r['cantidad']}x {r['medicamento']} ({r['indicacion']})" for r in recetas_pasadas]) if recetas_pasadas else "Sin receta."

                    lista_historial_ui.controls.append(ft.Card(elevation=2, content=ft.Container(padding=15, content=ft.Column([
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE_900), ft.Text(f"Atención: {fecha_str} | Dr. {h.get('medico_tratante','')}", weight="bold", color=ft.Colors.BLUE_900, size=16)]),
                        ft.Divider(height=10),
                        ft.Text(f"Motivo: {h.get('motivo','')}", weight="bold", color=ft.Colors.GREY_800),
                        ft.Text(f"Diagnóstico: {str_dx}", color=ft.Colors.RED_700, weight="bold"),
                        ft.Text(f"Plan de Trabajo: {h.get('plan_trabajo','')}", color=ft.Colors.BLUE_GREY_700),
                        ft.Text("Receta Emitida:", weight="bold", color=ft.Colors.ORANGE_800),
                        ft.Text(str_receta, color=ft.Colors.GREY_700)
                    ]))))

        # ==========================================
        # GUARDAR HISTORIA
        # ==========================================
        def guardar_historia(e):
            datos_clinicos = {
                "medico_tratante": nombre_medico,
                "motivo": in_motivo.value, "tiempo_enfermedad": in_tiempo_enf.value, "tipo_inicio": dp_tipo_inicio.value,
                "funciones_biologicas": { "apetito": in_apetito.value, "sed": in_sed.value, "orina": in_orina.value, "deposiciones": in_deposiciones.value, "sueno": in_sueno.value, "variacion_peso": in_peso_cambio.value },
                "antecedentes": { "cirugias": in_cirugias.value, "ram": in_ram.value, "egd": in_egd.value, "colonoscopia": in_colono.value, "hepatitis": chk_hepatitis.value },
                "habitos": { "cafe": chk_cafe.value, "gaseosas": chk_gaseosa.value, "ajies": chk_aji.value, "ceviches": chk_ceviche.value, "alcohol": chk_alcohol.value, "tabaco": chk_tabaco.value },
                "examen_fisico": { "fc": in_fc.value, "fr": in_fr.value, "pa": in_pa.value, "temp": in_temp.value, "sat": in_sat.value, "peso": in_peso_actual.value, "detalle": in_fisico.value },
                "diagnosticos": [in_dx1.value, in_dx2.value, in_dx3.value],
                "plan_trabajo": in_plan.value, 
                "receta": receta_actual, 
                "proxima_cita": in_cita.value,
                "archivos_adjuntos": archivos_adjuntos
            }
            try:
                PacientesRepository.guardar_historia_dinamica(dni_final, datos_clinicos)
                mostrar_mensaje("¡Historia Clínica guardada!", ft.Colors.GREEN_700)
                volver(e)
            except Exception as ex:
                mostrar_mensaje(f"Error al guardar: {ex}", ft.Colors.RED_700)

        # ==========================================
        # PESTAÑAS
        # ==========================================
        cont_1 = ft.Container(padding=20, content=ft.Column([
            ft.Text("ENFERMEDAD ACTUAL", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([in_tiempo_enf, dp_tipo_inicio], spacing=15),
            in_motivo, ft.Divider(height=20),
            ft.Text("FUNCIONES BIOLÓGICAS", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([in_apetito, in_sed, in_orina], wrap=True),
            ft.Row([in_deposiciones, in_sueno, in_peso_cambio], wrap=True),
        ], scroll=ft.ScrollMode.AUTO))

        cont_2 = ft.Container(padding=20, content=ft.Column([
            ft.Text("HÁBITOS DE CONSUMO", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([chk_cafe, chk_gaseosa, chk_aji, chk_ceviche, chk_alcohol, chk_tabaco], wrap=True),
            ft.Divider(height=10),
            ft.Text("ANTECEDENTES CLÍNICOS", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([in_cirugias, in_ram]), ft.Row([in_egd, in_colono]), chk_hepatitis,
            ft.Divider(height=10),
            ft.Text("SIGNOS VITALES (TRIAJE)", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([in_temp, in_sat, in_pa]), 
            ft.Row([in_fc, in_fr, in_peso_actual]), 
            ft.Divider(height=10),
            ft.Text("EXAMEN FÍSICO (MÉDICO)", weight="bold", color=ft.Colors.BLUE_900),
            in_fisico
        ], scroll=ft.ScrollMode.AUTO))

        cont_3 = ft.Container(padding=20, content=ft.Column([
            ft.Text("DIAGNÓSTICOS (DX)", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([in_dx1, in_dx2, in_dx3]), ft.Divider(height=20),
            ft.Text("PLAN DE TRABAJO (Exámenes, Dietas)", weight="bold", color=ft.Colors.BLUE_900),
            in_plan, in_cita, ft.Divider(height=20),
            
            ft.Text("ARCHIVOS ADJUNTOS (Exámenes, Endoscopias)", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([
                ft.ElevatedButton("Adjuntar Archivo", icon=ft.Icons.ATTACH_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=True))
            ]),
            lista_archivos_ui,
            ft.Divider(height=20),

            # --- BOTÓN DE IMPRESIÓN AÑADIDO AQUÍ ---
            ft.Row([
                ft.Text("RECETA MÉDICA", weight="bold", color=ft.Colors.ORANGE_800),
                ft.Container(expand=True),
                ft.ElevatedButton("🖨️ Imprimir Receta", bgcolor=ft.Colors.INDIGO_600, color="white", on_click=imprimir_receta)
            ]),
            contenedor_buscador, 
            lista_receta_ui
        ], scroll=ft.ScrollMode.AUTO))

        cont_4 = ft.Container(padding=20, content=ft.Column([ft.Text("HISTORIAL CLÍNICO DEL PACIENTE", weight="bold", color=ft.Colors.BLUE_900), lista_historial_ui], scroll=ft.ScrollMode.AUTO))

        area_contenido = ft.Container(content=cont_1, expand=True, bgcolor=ft.Colors.WHITE, border_radius=10)

        def cambiar_pestana(e, indice):
            if indice == 0: area_contenido.content = cont_1
            elif indice == 1: area_contenido.content = cont_2
            elif indice == 2: area_contenido.content = cont_3
            elif indice == 3: 
                cargar_historial_paciente() 
                area_contenido.content = cont_4
            for i, btn in enumerate(botones_pestanas):
                if i == indice: btn.bgcolor, btn.color = ft.Colors.BLUE_900, ft.Colors.WHITE
                else: btn.bgcolor, btn.color = ft.Colors.BLUE_GREY_100, ft.Colors.BLACK87
            if page: page.update()

        botones_pestanas = [
            ft.ElevatedButton("Anamnesis y Funciones", icon=ft.Icons.PERSON_SEARCH, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE, on_click=lambda e: cambiar_pestana(e, 0)),
            ft.ElevatedButton("Antecedentes y Físico", icon=ft.Icons.MEDICAL_INFORMATION, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: cambiar_pestana(e, 1)),
            ft.ElevatedButton("Diagnóstico y Receta", icon=ft.Icons.VACCINES, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: cambiar_pestana(e, 2)),
            ft.ElevatedButton("Ver Historial del Paciente", icon=ft.Icons.HISTORY, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: cambiar_pestana(e, 3))
        ]
        
        cuerpo_principal = ft.Column([
            ft.Row([ft.Icon(ft.Icons.ASSIGNMENT, size=30, color=ft.Colors.BLUE_900), ft.Text("Historia Clínica Especializada", size=22, weight="bold", color=ft.Colors.BLUE_900), ft.Container(expand=True), ft.ElevatedButton("Guardar y Finalizar Atención", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN_700, color="white", height=50, on_click=guardar_historia)]),
            ft.Divider(height=10),
            ft.Row(botones_pestanas, spacing=10, wrap=True),
            area_contenido
        ], expand=True)

        return ft.View(route=f"/paciente/{dni_final}/datos", appbar=barra_superior, controls=[ft.Container(content=cuerpo_principal, padding=20, expand=True, bgcolor=ft.Colors.BLUE_GREY_50)])

    except Exception as error_critico:
        return ft.View(route=f"/paciente/{dni_seleccionado or dni}/datos", controls=[ft.Container(content=ft.Column([ft.Text(f"Error:\n{traceback.format_exc()}")]), padding=40)])