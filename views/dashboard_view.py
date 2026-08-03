import flet as ft
import datetime
import traceback

def obtener_dashboard_view(page: ft.Page, on_navigate):
    try:
        from repositories.pacientes_repository import PacientesRepository
        from repositories.gestion_repository import GestionRepository
        from repositories.finanzas_repository import FinanzasRepository
        
        usuario = getattr(page, "usuario_actual", None)
        nombre_usuario = usuario["nombre"] if usuario else "Desconocido"
        rol_usuario = str(usuario.get("rol", "")).lower() if usuario else "sin rol"
        es_admin = rol_usuario in ["administrador", "admin"]

        barra_superior = ft.AppBar(
            leading=ft.Icon(ft.Icons.LOCAL_HOSPITAL, color="white"),
            title=ft.Text(f"Panel Principal | {nombre_usuario} ({rol_usuario.capitalize()})", color="white", size=18, weight="bold"),
            bgcolor=ft.Colors.BLUE_900,
            actions=[ft.TextButton(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color="white"), ft.Text("Cerrar Sesión", color="white")]), on_click=lambda _: [setattr(page, 'usuario_actual', None), on_navigate("/login")])]
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass 

        paciente_sel_dni, paciente_sel_nom = "", ""

        # ==========================================
        # 1. KPIs FINANCIEROS Y GASTOS
        # ==========================================
        t_ingresos, t_gastos, t_saldo = ft.Text("S/ 0.00", size=22, weight="bold", color=ft.Colors.GREEN_700), ft.Text("S/ 0.00", size=22, weight="bold", color=ft.Colors.RED_700), ft.Text("S/ 0.00", size=22, weight="bold", color=ft.Colors.BLUE_900)

        def actualizar_kpis(e=None):
            if es_admin:
                try:
                    res = FinanzasRepository.obtener_resumen_financiero_hoy()
                    t_ingresos.value, t_gastos.value, t_saldo.value = f"S/ {res['ingresos']:.2f}", f"S/ {res['gastos']:.2f}", f"S/ {res['saldo']:.2f}"
                    if page: page.update()
                except: pass

        in_gasto_con, in_gasto_mon, dp_gasto_met = ft.TextField(label="Concepto", width=250), ft.TextField(label="Monto (S/)", width=120, keyboard_type="number"), ft.Dropdown(label="Método", options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Yape/Plin")], width=140)

        def guardar_gasto(e):
            if not in_gasto_con.value or not in_gasto_mon.value: return
            FinanzasRepository.registrar_gasto(in_gasto_con.value.strip(), in_gasto_mon.value, dp_gasto_met.value, nombre_usuario)
            page.pop_dialog(); actualizar_kpis(e); mostrar_mensaje("Gasto registrado.", ft.Colors.GREEN_700)

        dlg_gasto = ft.AlertDialog(title=ft.Text("Registrar Gasto"), content=ft.Column([in_gasto_con, ft.Row([in_gasto_mon, dp_gasto_met])], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()), ft.ElevatedButton("Registrar", bgcolor=ft.Colors.RED_700, color="white", on_click=guardar_gasto)])

        # ==========================================
        # 2. GESTIÓN DE PERSONAL
        # ==========================================
        in_usr_id, in_usr_nom, in_usr_ape, in_usr_pwd = ft.TextField(label="ID Usuario", width=150), ft.TextField(label="Nombres", width=150), ft.TextField(label="Apellidos", width=150), ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=150)

        sw_caja = ft.Switch(label="Admisión/Caja", value=False)
        sw_triaje = ft.Switch(label="Triaje", value=False)
        sw_consultorio = ft.Switch(label="Consultorio/Historia", value=False)
        sw_farmacia = ft.Switch(label="Farmacia", value=False)
        sw_reportes = ft.Switch(label="Reportes", value=False)

        dp_usr_rol = ft.Dropdown(label="Rol (Plantilla)", width=150, options=[ft.dropdown.Option("ADMINISTRADOR"), ft.dropdown.Option("MEDICO"), ft.dropdown.Option("ENFERMERIA"), ft.dropdown.Option("FARMACIA"), ft.dropdown.Option("RECEPCION")])
        dp_usr_est = ft.Dropdown(label="Estado", width=120, value="ACTIVO", options=[ft.dropdown.Option("ACTIVO"), ft.dropdown.Option("INACTIVO")])

        def on_rol_change(e):
            r = dp_usr_rol.value
            sw_caja.value = r in ["ADMINISTRADOR", "RECEPCION"]
            sw_triaje.value = r in ["ADMINISTRADOR", "ENFERMERIA"]
            sw_consultorio.value = r in ["ADMINISTRADOR", "MEDICO"]
            sw_farmacia.value = r in ["ADMINISTRADOR", "FARMACIA"]
            sw_reportes.value = r in ["ADMINISTRADOR"]
            if page: page.update()

        dp_usr_rol.on_change = on_rol_change
        lst_usuarios = ft.ListView(height=200, spacing=5)

        def cargar_usuarios(e=None):
            lst_usuarios.controls.clear()
            for u in GestionRepository.obtener_todos_los_usuarios():
                rb, ce = str(u.get('rol', '')).upper(), ft.Colors.GREEN_600 if str(u.get('estado','')).upper()=="ACTIVO" else ft.Colors.RED_600
                cb = ft.Colors.RED_700 if rb in ["ADMINISTRADOR","ADMIN"] else ft.Colors.BLUE_700
                lst_usuarios.controls.append(ft.Container(padding=10, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=8, content=ft.Row([ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ce, size=30), ft.Column([ft.Text(f"{u.get('nombres','')} {u.get('apellidos','')}", weight="bold", size=13), ft.Text(f"ID: {u['username']}", size=11)], expand=True), ft.Container(content=ft.Text(rb, color="white", size=10, weight="bold"), bgcolor=cb, padding=5, border_radius=4), ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE_700, on_click=lambda ev, usr=u: load_usr(usr))])))
            if page: page.update()

        def load_usr(usr):
            in_usr_id.value, in_usr_id.disabled, in_usr_nom.value, in_usr_ape.value, in_usr_pwd.value, dp_usr_rol.value, dp_usr_est.value = usr['username'], True, usr.get('nombres', ''), usr.get('apellidos', ''), "", usr.get('rol', '').upper(), usr.get('estado', 'ACTIVO').upper()

            p = usr.get("permisos", {})
            sw_caja.value = p.get("caja", False)
            sw_triaje.value = p.get("triaje", False)
            sw_consultorio.value = p.get("consultorio", False)
            sw_farmacia.value = p.get("farmacia", False)
            sw_reportes.value = p.get("reportes", False)

            page.update()

        def save_usr(e):
            if not in_usr_id.value or not in_usr_nom.value or not dp_usr_rol.value: return
            p = {
                "caja": sw_caja.value, "triaje": sw_triaje.value,
                "consultorio": sw_consultorio.value, "farmacia": sw_farmacia.value, "reportes": sw_reportes.value
            }
            GestionRepository.guardar_usuario(in_usr_id.value.strip().lower(), in_usr_nom.value.strip(), in_usr_ape.value.strip(), dp_usr_rol.value, in_usr_pwd.value.strip(), dp_usr_est.value, p)
            in_usr_id.value, in_usr_nom.value, in_usr_ape.value, in_usr_pwd.value, in_usr_id.disabled, dp_usr_rol.value = "", "", "", "", False, None
            sw_caja.value, sw_triaje.value, sw_consultorio.value, sw_farmacia.value, sw_reportes.value = False, False, False, False, False
            cargar_usuarios(e)

        dlg_usuarios = ft.AlertDialog(title=ft.Text("Personal"), content=ft.Container(width=650, content=ft.Column([
            ft.Row([in_usr_id, in_usr_nom, in_usr_ape], wrap=True),
            ft.Row([dp_usr_rol, in_usr_pwd, dp_usr_est], wrap=True),
            ft.Text("Permisos Especiales:", weight="bold", color=ft.Colors.BLUE_900),
            ft.Row([sw_caja, sw_triaje, sw_consultorio, sw_farmacia, sw_reportes], wrap=True),
            ft.ElevatedButton("Guardar", bgcolor=ft.Colors.GREEN_700, color="white", on_click=save_usr),
            ft.Divider(), lst_usuarios
        ], tight=True)), actions=[ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())])

        def abrir_admin(e):
            in_usr_id.value, in_usr_nom.value, in_usr_ape.value, in_usr_pwd.value, in_usr_id.disabled, dp_usr_rol.value = "", "", "", "", False, None
            cargar_usuarios(e); page.show_dialog(dlg_usuarios)

        # ==========================================
        # 3. CREACIÓN DE PACIENTES
        # ==========================================
        in_p_dni = ft.TextField(label="DNI", width=150, max_length=8, keyboard_type="number", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
        in_p_tel = ft.TextField(label="Teléfono", width=150, max_length=9, keyboard_type="number", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
        in_p_nom, in_p_ape = ft.TextField(label="Nombres", width=200), ft.TextField(label="Apellidos", width=200)
        in_p_correo = ft.TextField(label="Correo Electrónico", width=200)
        in_p_dir = ft.TextField(label="Dirección", width=200)
        in_p_historia = ft.TextField(label="N° Historia Física", width=150)

        def save_pac(e):
            if not in_p_dni.value or not in_p_nom.value or not in_p_ape.value: return

            # Simple email validation logic
            correo = in_p_correo.value.strip()
            if correo and "@" not in correo:
                mostrar_mensaje("Por favor, ingrese un correo válido.", ft.Colors.RED_700)
                return

            PacientesRepository.registrar_paciente(
                in_p_dni.value.strip(), in_p_nom.value.strip(), in_p_ape.value.strip(), in_p_tel.value.strip(),
                correo, in_p_dir.value.strip(), in_p_historia.value.strip()
            )
            page.pop_dialog(); ejecutar_busqueda(e)

        dlg_paciente = ft.AlertDialog(title=ft.Text("Datos Paciente"), content=ft.Column([ft.Row([in_p_dni, in_p_tel, in_p_historia]), ft.Row([in_p_nom, in_p_ape]), ft.Row([in_p_correo, in_p_dir])], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()), ft.ElevatedButton("Guardar", bgcolor=ft.Colors.GREEN_700, color="white", on_click=save_pac)])

        def abrir_modal_paciente(dni="", nom="", ape="", tel="", correo="", dir="", hist="", edit=False):
            in_p_dni.value, in_p_dni.disabled = dni, edit
            in_p_nom.value, in_p_ape.value, in_p_tel.value = nom, ape, tel
            in_p_correo.value, in_p_dir.value, in_p_historia.value = correo, dir, hist
            if edit: page.pop_dialog()
            page.show_dialog(dlg_paciente)

        # ==========================================
        # 4. ADMISIÓN Y CAJA
        # ==========================================
        dp_esp, in_monto, in_aut, dp_met = ft.Dropdown(label="Especialidad", options=[ft.dropdown.Option("Medicina General"), ft.dropdown.Option("Gastroenterología"), ft.dropdown.Option("Pediatría")], width=250), ft.TextField(label="Monto", value="50.00", width=100), ft.TextField(label="Firma Cortesía", width=250, disabled=True), ft.Dropdown(label="Método", options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Yape"), ft.dropdown.Option("Plin"), ft.dropdown.Option("Cortesía")], width=120)
        
        def cambia_met(e):
            if dp_met.value == "Cortesía": in_monto.value, in_monto.disabled, in_aut.disabled = "0.00", True, False
            else: in_monto.value, in_monto.disabled, in_aut.disabled = "50.00", False, True
            page.update()
        dp_met.on_select = cambia_met

        def cobrar(e):
            if not dp_esp.value or not dp_met.value: return
            GestionRepository.registrar_admision(paciente_sel_dni, paciente_sel_nom, dp_esp.value, "0.00" if dp_met.value=="Cortesía" else in_monto.value, dp_met.value, in_aut.value)
            page.pop_dialog(); actualizar_kpis(e); mostrar_mensaje("¡Paciente a Triaje!", ft.Colors.GREEN_700)

        dlg_admision = ft.AlertDialog(title=ft.Text("Caja"), content=ft.Column([dp_esp, ft.Row([dp_met, in_monto]), in_aut], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()), ft.ElevatedButton("Cobrar", bgcolor=ft.Colors.GREEN_600, color="white", on_click=cobrar)])

        def opciones_pac(dni, nom, ape, tel, correo="", dir="", hist=""):
            nonlocal paciente_sel_dni, paciente_sel_nom
            paciente_sel_dni, paciente_sel_nom = dni, f"{nom} {ape}"
            btn = []
            permisos = usuario.get("permisos", {}) if usuario else {}
            if permisos.get("caja", es_admin or rol_usuario == "recepcion"):
                btn.append(ft.ElevatedButton("Cobrar Consulta", icon=ft.Icons.POINT_OF_SALE, bgcolor=ft.Colors.GREEN_600, color="white", width=250, on_click=lambda _: [page.pop_dialog(), page.show_dialog(dlg_admision)]))
                btn.append(ft.ElevatedButton("Editar Datos", icon=ft.Icons.EDIT, bgcolor=ft.Colors.BLUE_GREY_600, color="white", width=250, on_click=lambda _: abrir_modal_paciente(dni, nom, ape, tel, correo, dir, hist, True)))
            if permisos.get("consultorio", es_admin or rol_usuario == "medico"):
                btn.append(ft.ElevatedButton("Historia Clínica", icon=ft.Icons.FOLDER_SHARED, bgcolor=ft.Colors.BLUE_700, color="white", width=250, on_click=lambda _: [page.pop_dialog(), on_navigate(f"/paciente/{dni}/datos")]))
            page.show_dialog(ft.AlertDialog(title=ft.Text(paciente_sel_nom, size=16), content=ft.Column(btn, tight=True), actions=[ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())]))

        # ==========================================
        # 5. COLA MÉDICA (IZQUIERDA)
        # ==========================================
        lst_cola = ft.ListView(expand=True, spacing=10)
        
        def cargar_cola(e=None):
            lst_cola.controls.clear()
            pacs = GestionRepository.obtener_cola_consultorio()
            if not pacs: lst_cola.controls.append(ft.Text("Consultorio vacío.", color=ft.Colors.GREY_500, italic=True))
            else:
                for turno, t in enumerate(pacs, 1): lst_cola.controls.append(ft.Card(elevation=1, content=ft.Container(padding=10, bgcolor=ft.Colors.BLUE_50, content=ft.Row([ft.CircleAvatar(content=ft.Text(f"#{turno}", color="white"), bgcolor=ft.Colors.BLUE_800), ft.Column([ft.Text(t.get("nombre_paciente", ""), weight="bold"), ft.Text(f"DNI: {t.get('dni')}", size=11)], expand=True), ft.ElevatedButton("Atender", bgcolor=ft.Colors.BLUE_800, color="white", on_click=lambda ev, d=t['dni'], id_a=t['id_admision']: [GestionRepository.actualizar_estado_admision(id_a, "En Atención"), on_navigate(f"/paciente/{d}/datos")])]))))
            if page: page.update()

        # ==========================================
        # 6. ARCHIVO HISTÓRICO (DERECHA)
        # ==========================================
        lst_pacientes, in_busqueda = ft.ListView(expand=True, spacing=10), ft.TextField(label="Buscar DNI o Apellido", prefix_icon=ft.Icons.SEARCH, expand=True)

        def ejecutar_busqueda(e=None):
            q = str(in_busqueda.value).strip()
            lst_pacientes.controls.clear()
            if not q: lst_pacientes.controls.append(ft.Text("Ingrese búsqueda...", color=ft.Colors.GREY_500, italic=True))
            else:
                for d in PacientesRepository.buscar_paciente_mixto(q):
                    lst_pacientes.controls.append(
                        ft.Card(content=ft.Container(content=ft.ListTile(
                            leading=ft.CircleAvatar(content=ft.Text("P"), bgcolor=ft.Colors.BLUE_700),
                            title=ft.Text(f"{d.get('apellidos','')}, {d.get('nombres','')}", weight="bold"),
                            subtitle=ft.Text(f"DNI: {d.get('dni','')} | Tel: {d.get('telefono','')}"),
                            on_click=lambda ev, d1=d.get('dni',''), n=d.get('nombres',''), a=d.get('apellidos',''), t=d.get('telefono',''), c=d.get('correo',''), dir=d.get('direccion',''), h=d.get('historia_fisica',''): opciones_pac(d1, n, a, t, c, dir, h)
                        ), padding=5))
                    )
            if page: page.update()
        in_busqueda.on_submit = ejecutar_busqueda

        # ==========================================
        # ENSAMBLAJE DE LA VISTA
        # ==========================================
        seccion_superior, row_modulos = ft.Column(spacing=10), ft.Row(wrap=True)
        permisos = usuario.get("permisos", {}) if usuario else {}
        if permisos.get("caja", es_admin or rol_usuario == "recepcion"):
            row_modulos.controls.append(ft.ElevatedButton("Nuevo Paciente", icon=ft.Icons.PERSON_ADD, bgcolor=ft.Colors.GREEN_700, color="white", on_click=lambda _: abrir_modal_paciente()))
            row_modulos.controls.append(ft.ElevatedButton("Agenda de Citas", icon=ft.Icons.CALENDAR_MONTH, bgcolor=ft.Colors.DEEP_PURPLE_700, color="white", on_click=lambda _: on_navigate("/agenda")))
        if permisos.get("triaje", es_admin or rol_usuario == "enfermeria"):
            row_modulos.controls.append(ft.ElevatedButton("Ir a Triaje", icon=ft.Icons.MEDICAL_SERVICES, bgcolor=ft.Colors.TEAL_700, color="white", on_click=lambda _: on_navigate("/triaje")))
        if permisos.get("farmacia", es_admin or rol_usuario == "farmacia"):
            row_modulos.controls.append(ft.ElevatedButton("Farmacia", icon=ft.Icons.LOCAL_PHARMACY, bgcolor=ft.Colors.ORANGE_700, color="white", on_click=lambda _: on_navigate("/farmacia")))
        
        if permisos.get("reportes", es_admin):
            row_modulos.controls.append(ft.ElevatedButton("Registrar Gasto", icon=ft.Icons.MONEY_OFF, bgcolor=ft.Colors.RED_700, color="white", on_click=lambda _: page.show_dialog(dlg_gasto)))
            row_modulos.controls.append(ft.ElevatedButton("Personal", icon=ft.Icons.ADMIN_PANEL_SETTINGS, bgcolor=ft.Colors.BLUE_GREY_800, color="white", on_click=abrir_admin))
            row_modulos.controls.append(ft.ElevatedButton("Reportes y Caja", icon=ft.Icons.ANALYTICS, bgcolor=ft.Colors.INDIGO_900, color="white", on_click=lambda _: on_navigate("/reportes")))

        seccion_superior.controls.append(row_modulos)

        if es_admin:
            seccion_superior.controls.append(ft.Row([ft.Card(content=ft.Container(content=ft.Column([ft.Text("INGRESOS HOY", weight="bold"), t_ingresos]), padding=15), expand=True), ft.Card(content=ft.Container(content=ft.Column([ft.Text("GASTOS HOY", weight="bold"), t_gastos]), padding=15), expand=True), ft.Card(content=ft.Container(content=ft.Column([ft.Text("SALDO", weight="bold"), t_saldo]), padding=15), expand=True)]))

        panel_izq = ft.Container(expand=4, bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, content=ft.Column([ft.Row([ft.Icon(ft.Icons.MEETING_ROOM, color=ft.Colors.BLUE_900), ft.Text("Pacientes en Puerta", weight="bold", color=ft.Colors.BLUE_900), ft.Container(expand=True), ft.IconButton(icon=ft.Icons.REFRESH, on_click=cargar_cola)]), ft.Divider(), lst_cola]))
        panel_der = ft.Container(expand=6, bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, content=ft.Column([ft.Row([ft.Icon(ft.Icons.FOLDER_SHARED, color=ft.Colors.BLUE_900), ft.Text("Archivo Histórico", weight="bold", color=ft.Colors.BLUE_900)]), ft.Row([in_busqueda, ft.ElevatedButton("Buscar", icon=ft.Icons.SEARCH, bgcolor=ft.Colors.BLUE_700, color="white", on_click=ejecutar_busqueda)]), lst_pacientes]))
        
        ejecutar_busqueda(None); actualizar_kpis(None); cargar_cola(None)

        return ft.View(route="/", appbar=barra_superior, controls=[ft.Container(content=ft.Column([seccion_superior, ft.Divider(), ft.Row([panel_izq, panel_der], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)], expand=True), padding=15, expand=True, bgcolor=ft.Colors.BLUE_GREY_50)])

    except Exception as error_critico:
        return ft.View(route="/", controls=[ft.Container(content=ft.Column([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_700, size=80), ft.Text("¡Error Crítico!", size=24, weight="bold", color=ft.Colors.RED_700), ft.Container(content=ft.Text(f"{traceback.format_exc()}", color="white", selectable=True), bgcolor=ft.Colors.BLACK87, padding=20, border_radius=10, expand=True), ft.ElevatedButton("Volver", on_click=lambda _: on_navigate("/login"))]), padding=40, expand=True)])