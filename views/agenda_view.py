import flet as ft
import traceback
import datetime

def obtener_agenda_view(page: ft.Page, on_navigate):
    try:
        from repositories.agenda_repository import AgendaRepository
        from repositories.gestion_repository import GestionRepository

        usuario = getattr(page, "usuario_actual", None) or {}
        nombre_usuario = usuario.get("nombres", "Recepción")
        rol_usuario = str(usuario.get("rol", "")).lower()

        barra_superior = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Volver al Panel", icon_color="white", on_click=lambda _: on_navigate("/")),
            title=ft.Text(f"Agenda de Citas | {nombre_usuario}", color="white", size=18, weight="bold"),
            bgcolor=ft.Colors.DEEP_PURPLE_800
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass

        # Controles UI
        # Usamos TextFields temporales ya que Flet no tiene DatePicker avanzado listado en todos los entornos,
        # pero es suficiente para el flujo
        hoy_str = datetime.datetime.now().strftime("%Y-%m-%d")
        in_fecha_busqueda = ft.TextField(label="Fecha (YYYY-MM-DD)", value=hoy_str, width=200)
        lista_citas = ft.ListView(expand=True, spacing=10)

        # Modal Nueva Cita
        in_nc_dni = ft.TextField(label="DNI Paciente", width=150)
        in_nc_nom = ft.TextField(label="Nombre Paciente", expand=True)
        in_nc_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", value=hoy_str, width=150)
        in_nc_hora = ft.TextField(label="Hora (HH:MM)", width=120)

        # Obtener médicos para el dropdown
        medicos = [u for u in GestionRepository.obtener_todos_los_usuarios() if u.get("rol", "").upper() in ["MEDICO", "ADMINISTRADOR"]]
        opciones_medicos = [ft.dropdown.Option(key=m['username'], text=f"Dr. {m.get('nombres', '')} {m.get('apellidos', '')}") for m in medicos]
        if not opciones_medicos:
            opciones_medicos = [ft.dropdown.Option(key="medico1", text="Dr. General")]

        dp_nc_medico = ft.Dropdown(label="Médico", options=opciones_medicos, expand=True)
        in_nc_motivo = ft.TextField(label="Motivo", expand=True)

        def cargar_agenda(e=None):
            fecha = in_fecha_busqueda.value.strip()
            lista_citas.controls.clear()

            try:
                citas = AgendaRepository.obtener_citas_por_fecha(fecha)
                if not citas:
                    lista_citas.controls.append(ft.Text(f"No hay citas para el {fecha}.", color=ft.Colors.GREY_500, italic=True))
                else:
                    for c in citas:
                        est = c.get("estado", "Pendiente")
                        color_est = ft.Colors.ORANGE_600 if est == "Pendiente" else ft.Colors.GREEN_600 if est == "Atendido" else ft.Colors.RED_600

                        btn_atendido = ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, icon_color=ft.Colors.GREEN_600, tooltip="Marcar Atendido", on_click=lambda ev, cid=c['id']: actualizar_cita(cid, "Atendido"))
                        btn_cancelar = ft.IconButton(icon=ft.Icons.CANCEL, icon_color=ft.Colors.RED_600, tooltip="Cancelar", on_click=lambda ev, cid=c['id']: actualizar_cita(cid, "Cancelado"))

                        acciones = ft.Row([btn_atendido, btn_cancelar]) if est == "Pendiente" else ft.Text(est, color=color_est, weight="bold")

                        tarjeta = ft.Card(
                            elevation=2,
                            content=ft.Container(
                                padding=15,
                                border=ft.border.Border(left=ft.border.BorderSide(width=5, color=color_est)),
                                content=ft.Row([
                                    ft.Column([
                                        ft.Text(c.get("hora", "00:00"), size=20, weight="bold", color=ft.Colors.DEEP_PURPLE_900),
                                        ft.Text(est, size=12, color=color_est)
                                    ], alignment=ft.MainAxisAlignment.CENTER),
                                    ft.VerticalDivider(width=20),
                                    ft.Column([
                                        ft.Text(c.get("nombre_paciente", "Paciente"), weight="bold", size=16),
                                        ft.Text(f"DNI: {c.get('dni_paciente', '')} | Médico: {c.get('nombre_medico', '')}", size=12, color=ft.Colors.GREY_700),
                                        ft.Text(f"Motivo: {c.get('motivo', '')}", size=12, color=ft.Colors.GREY_600, italic=True),
                                    ], expand=True),
                                    acciones
                                ])
                            )
                        )
                        lista_citas.controls.append(tarjeta)
            except Exception as ex:
                lista_citas.controls.append(ft.Text(f"Error cargando agenda: {ex}", color=ft.Colors.RED_700))

            if page: page.update()

        def actualizar_cita(id_cita, estado):
            try:
                AgendaRepository.actualizar_estado_cita(id_cita, estado)
                mostrar_mensaje(f"Cita marcada como {estado}.", ft.Colors.GREEN_700)
                cargar_agenda()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        def guardar_cita(e):
            if not in_nc_dni.value or not in_nc_fecha.value or not in_nc_hora.value or not dp_nc_medico.value:
                return mostrar_mensaje("Complete los campos obligatorios.", ft.Colors.RED_700)

            # Validar que no haya cruce de horarios para el mismo médico
            try:
                citas_dia = AgendaRepository.obtener_citas_por_fecha(in_nc_fecha.value)
                for c in citas_dia:
                    if c.get("id_medico") == dp_nc_medico.value and c.get("hora") == in_nc_hora.value and c.get("estado") == "Pendiente":
                        return mostrar_mensaje(f"El médico ya tiene una cita a las {in_nc_hora.value}", ft.Colors.RED_700)
            except: pass

            nombre_medico = next((opt.text for opt in dp_nc_medico.options if opt.key == dp_nc_medico.value), "Médico")

            try:
                AgendaRepository.registrar_cita(
                    in_nc_dni.value.strip(), in_nc_nom.value.strip(),
                    dp_nc_medico.value, nombre_medico,
                    in_nc_fecha.value.strip(), in_nc_hora.value.strip(),
                    in_nc_motivo.value.strip()
                )
                mostrar_mensaje("Cita registrada exitosamente.", ft.Colors.GREEN_700)
                page.pop_dialog()
                in_fecha_busqueda.value = in_nc_fecha.value
                cargar_agenda()

                # Limpiar modal
                in_nc_dni.value, in_nc_nom.value, in_nc_hora.value, in_nc_motivo.value = "", "", "", ""
            except Exception as ex:
                mostrar_mensaje(f"Error al guardar: {ex}", ft.Colors.RED_700)

        dlg_nueva_cita = ft.AlertDialog(
            title=ft.Text("Nueva Cita"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([in_nc_dni, in_nc_nom]),
                    ft.Row([in_nc_fecha, in_nc_hora]),
                    ft.Row([dp_nc_medico]),
                    in_nc_motivo
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                ft.ElevatedButton("Guardar Cita", bgcolor=ft.Colors.DEEP_PURPLE_700, color="white", on_click=guardar_cita)
            ]
        )

        cuerpo_principal = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, size=30, color=ft.Colors.DEEP_PURPLE_800),
                ft.Text("Gestión de Agenda", size=24, weight="bold", color=ft.Colors.DEEP_PURPLE_900),
                ft.Container(expand=True),
                ft.ElevatedButton("Nueva Cita", icon=ft.Icons.ADD, bgcolor=ft.Colors.GREEN_700, color="white", on_click=lambda _: page.show_dialog(dlg_nueva_cita))
            ]),
            ft.Divider(height=20),
            ft.Row([
                in_fecha_busqueda,
                ft.ElevatedButton("Buscar", icon=ft.Icons.SEARCH, bgcolor=ft.Colors.DEEP_PURPLE_600, color="white", on_click=cargar_agenda)
            ]),
            ft.Container(
                content=lista_citas,
                expand=True,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                padding=20
            )
        ], expand=True)

        cargar_agenda()

        return ft.View(
            route="/agenda",
            appbar=barra_superior,
            controls=[
                ft.Container(
                    content=cuerpo_principal,
                    padding=20,
                    expand=True,
                    bgcolor=ft.Colors.BLUE_GREY_50
                )
            ]
        )

    except Exception as error_critico:
        return ft.View(route="/agenda", controls=[ft.Container(content=ft.Column([ft.Text(f"Error en Agenda:\n{traceback.format_exc()}")]), padding=40)])
