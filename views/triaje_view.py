import flet as ft
import traceback

def obtener_triaje_view(page: ft.Page, on_navigate):
    try:
        from repositories.pacientes_repository import PacientesRepository
        from repositories.gestion_repository import GestionRepository
        
        usuario = getattr(page, "usuario_actual", None)
        nombre_usuario = usuario["nombre"] if usuario else "Enfermería"

        barra_superior = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Volver al Panel", icon_color="white", on_click=lambda _: on_navigate("/")),
            title=ft.Text(f"Módulo de Triaje | {nombre_usuario}", color="white", size=18, weight="bold"),
            bgcolor=ft.Colors.TEAL_800,
            actions=[ft.TextButton(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color="white"), ft.Text("Cerrar Sesión", color="white")]), on_click=lambda _: [setattr(page, 'usuario_actual', None), on_navigate("/login")])]
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass

        lista_cola = ft.ListView(expand=True, spacing=10)
        estado_triaje = {"id_admision": None, "dni": None, "nombre": None}

        texto_paciente = ft.Text("Seleccione un paciente de la lista", size=20, weight="bold", color=ft.Colors.GREY_500)
        texto_dni = ft.Text("", size=14, color=ft.Colors.GREY_500)
        
        input_peso, input_talla = ft.TextField(label="Peso (kg)", width=120, disabled=True), ft.TextField(label="Talla (m)", width=120, disabled=True)
        input_fc, input_fr, input_pa = ft.TextField(label="F.C. (LPM)", width=100, disabled=True), ft.TextField(label="F.R. (RPM)", width=100, disabled=True), ft.TextField(label="P.A.", width=120, disabled=True)
        input_temp, input_sat = ft.TextField(label="Temp. (°C)", width=100, disabled=True), ft.TextField(label="SpO2 (%)", width=100, disabled=True)
        
        btn_guardar = ft.ElevatedButton("Guardar Signos y Derivar", icon=ft.Icons.CHECK, bgcolor=ft.Colors.TEAL_700, color="white", height=50, disabled=True)

        # ----------------------------------------------------
        # SOLUCIÓN: SEPARAMOS EL BOTÓN DE LOS CUADROS DE TEXTO
        # ----------------------------------------------------
        def limpiar_panel_derecho():
            estado_triaje.update({"id_admision": None, "dni": None, "nombre": None})
            texto_paciente.value, texto_paciente.color = "Seleccione un paciente de la lista", ft.Colors.GREY_500
            texto_dni.value = ""
            
            # Limpiamos solo los inputs
            for c in [input_peso, input_talla, input_fc, input_fr, input_pa, input_temp, input_sat]: 
                c.value = ""
                c.disabled = True
            
            # El botón se desactiva por separado
            btn_guardar.disabled = True
            if page: page.update()

        def seleccionar_paciente(id_admision, dni, nombre):
            estado_triaje.update({"id_admision": id_admision, "dni": dni, "nombre": nombre})
            texto_paciente.value, texto_paciente.color, texto_dni.value = f"Paciente: {nombre}", ft.Colors.TEAL_900, f"DNI: {dni}"
            
            # Activamos y vaciamos solo los inputs
            for c in [input_peso, input_talla, input_fc, input_fr, input_pa, input_temp, input_sat]: 
                c.value = ""
                c.disabled = False
            
            # El botón se activa por separado
            btn_guardar.disabled = False
            if page: page.update()
        # ----------------------------------------------------

        def guardar_triage_y_derivar(e):
            if not input_peso.value or not input_talla.value: return mostrar_mensaje("Debe ingresar peso y talla.", ft.Colors.RED_700)
            try:
                p, t = float(input_peso.value), float(input_talla.value)
                PacientesRepository.guardar_signos_vitales(estado_triaje["dni"], p, t, p/(t*t) if t>0 else 0, str(input_fc.value), str(input_fr.value), str(input_pa.value), str(input_temp.value), str(input_sat.value))
                GestionRepository.actualizar_estado_admision(estado_triaje["id_admision"], "Listo para Consultorio")
                mostrar_mensaje(f"✅ Triaje de {estado_triaje['nombre']} completado.", ft.Colors.GREEN_700)
                limpiar_panel_derecho(); cargar_cola_espera(e) 
            except Exception as ex: mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        btn_guardar.on_click = guardar_triage_y_derivar
        panel_derecho = ft.Container(bgcolor=ft.Colors.WHITE, padding=30, border_radius=10, expand=5, content=ft.Column([ft.Icon(ft.Icons.MONITOR_HEART, size=50, color=ft.Colors.TEAL_200), texto_paciente, texto_dni, ft.Divider(height=30), ft.Text("Signos Vitales Normativos:", weight="bold", color=ft.Colors.BLUE_GREY_700), ft.Row([input_temp, input_sat, input_pa], spacing=20), ft.Row([input_fc, input_fr, input_peso, input_talla], spacing=20), ft.Container(height=20), btn_guardar]))

        def cargar_cola_espera(e=None):
            lista_cola.controls.clear()
            pacs = GestionRepository.obtener_cola_triaje()
            if not pacs: lista_cola.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=50, color=ft.Colors.GREY_400), ft.Text("No hay pacientes esperando.", weight="bold", color=ft.Colors.GREY_500)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.CENTER), padding=40))
            else:
                for turno, tk in enumerate(pacs, 1): lista_cola.controls.append(ft.Card(elevation=1, content=ft.Container(padding=10, bgcolor=ft.Colors.WHITE, content=ft.Row([ft.CircleAvatar(content=ft.Text(f"#{turno}", weight="bold", color="white"), bgcolor=ft.Colors.TEAL_600), ft.Column([ft.Text(tk.get("nombre_paciente", ""), size=14, weight="bold"), ft.Text(f"Derivado a: {tk.get('especialidad')}", color=ft.Colors.GREY_600, size=11)], expand=True), ft.IconButton(icon=ft.Icons.ARROW_FORWARD_IOS, icon_color=ft.Colors.TEAL_700, on_click=lambda ev, id_a=tk.get('id_admision'), d=tk.get('dni'), n=tk.get("nombre_paciente", ""): seleccionar_paciente(id_a, d, n))]))))
            if page: page.update()

        panel_izquierdo = ft.Container(expand=4, content=ft.Column([ft.Row([ft.Icon(ft.Icons.PEOPLE_ALT, color=ft.Colors.TEAL_800), ft.Text("En Espera", size=18, weight="bold", color=ft.Colors.TEAL_900), ft.Container(expand=True), ft.IconButton(icon=ft.Icons.REFRESH, on_click=cargar_cola_espera)]), ft.Divider(), lista_cola]))
        cargar_cola_espera()

        return ft.View(route="/triaje", appbar=barra_superior, controls=[ft.Container(content=ft.Row([panel_izquierdo, ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT), panel_derecho], expand=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START), padding=20, expand=True, bgcolor=ft.Colors.BLUE_GREY_50)])

    except Exception as error_critico:
        return ft.View(route="/triaje", controls=[ft.Container(content=ft.Column([ft.Text(f"Error en Triaje:\n{traceback.format_exc()}")]), padding=40)])