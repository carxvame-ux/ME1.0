import flet as ft
import traceback
import pandas as pd
import datetime
import os

def obtener_reportes_view(page: ft.Page, on_navigate):
    try:
        from repositories.finanzas_repository import FinanzasRepository
        from repositories.farmacia_repository import FarmaciaRepository
        
        # BLINDAJE ANTI-CRASH PARA LEER EL USUARIO
        usuario = getattr(page, "usuario_actual", None) or {}
        nombre_usuario = usuario.get("nombres", usuario.get("nombre", "Administrador"))
        rol_usuario = str(usuario.get("rol", "sin rol")).lower()

        # BLOQUEO ELEGANTE - Ahora manejado por main.py y permisos dinámicos
        permisos = usuario.get("permisos", {})
        if not permisos.get("reportes", rol_usuario in ["administrador", "admin"]):
            pantalla_bloqueo = ft.Column([
                ft.Icon(ft.Icons.LOCK, color=ft.Colors.RED_700, size=80),
                ft.Text("ACCESO DENEGADO", color=ft.Colors.RED_700, size=30, weight="bold"),
                ft.Text("No tienes permisos para ver la caja y reportes.", color=ft.Colors.GREY_700, size=16),
                ft.Container(height=20),
                ft.ElevatedButton("Volver al Inicio", icon=ft.Icons.ARROW_BACK, on_click=lambda _: on_navigate("/"))
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            return ft.View(route="/reportes", controls=[ft.Container(content=pantalla_bloqueo, alignment=ft.alignment.center, expand=True)])

        def volver(e=None): on_navigate("/")

        barra_superior = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Volver al Panel", icon_color="white", on_click=volver),
            title=ft.Text(f"Inteligencia de Negocios y Cierre de Caja | {nombre_usuario}", color="white", size=18, weight="bold"),
            bgcolor=ft.Colors.INDIGO_900
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass

        # ==========================================
        # TAB 1: FLUJO DE CAJA DEL DÍA
        # ==========================================
        tabla_movimientos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Hora", weight="bold")), ft.DataColumn(ft.Text("Tipo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")), ft.DataColumn(ft.Text("Descripción", weight="bold")),
                ft.DataColumn(ft.Text("Método", weight="bold")), ft.DataColumn(ft.Text("Monto (S/)", weight="bold"), numeric=True),
            ], rows=[]
        )

        t_efectivo = ft.Text("S/ 0.00", size=20, weight="bold", color=ft.Colors.GREEN_700)
        t_digital = ft.Text("S/ 0.00", size=20, weight="bold", color=ft.Colors.BLUE_700)
        t_egresos = ft.Text("S/ 0.00", size=20, weight="bold", color=ft.Colors.RED_700)
        t_neto = ft.Text("S/ 0.00", size=24, weight="bold", color=ft.Colors.INDIGO_900)

        movimientos_crudos = []

        def cargar_flujo_caja():
            nonlocal movimientos_crudos
            movimientos_crudos = FinanzasRepository.obtener_detalles_financieros_hoy()
            tabla_movimientos.rows.clear()
            
            efectivo, digital, egresos = 0.0, 0.0, 0.0
            for m in movimientos_crudos:
                monto_str = f"+ {m['monto']:.2f}" if m["tipo"] == "INGRESO" else f"- {m['monto']:.2f}"
                tabla_movimientos.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(m["hora"])), ft.DataCell(ft.Text(m["tipo"], weight="bold", color=ft.Colors.GREEN_700 if m["tipo"] == "INGRESO" else ft.Colors.RED_700)),
                    ft.DataCell(ft.Text(m["categoria"])), ft.DataCell(ft.Text(m["descripcion"])),
                    ft.DataCell(ft.Text(m["metodo"])), ft.DataCell(ft.Text(monto_str, weight="bold"))
                ]))
                if m["tipo"] == "INGRESO":
                    if m["metodo"].upper() == "EFECTIVO": efectivo += m["monto"]
                    else: digital += m["monto"] 
                else: egresos += m["monto"]
            
            t_efectivo.value = f"S/ {efectivo:.2f}"
            t_digital.value = f"S/ {digital:.2f}"
            t_egresos.value = f"S/ {egresos:.2f}"
            t_neto.value = f"S/ {(efectivo + digital) - egresos:.2f}"
            
            if page: page.update()

        def exportar_excel(e):
            if not movimientos_crudos: return mostrar_mensaje("No hay movimientos para exportar hoy.", ft.Colors.RED_700)
            try:
                df = pd.DataFrame(movimientos_crudos)
                if 'id' in df.columns: df = df.drop(columns=['id'])
                fecha_hoy = datetime.datetime.now().strftime("%Y%m%d")
                ruta_descargas = os.path.join(os.path.expanduser('~'), 'Downloads', f'Cierre_Caja_{fecha_hoy}.xlsx')
                df.to_excel(ruta_descargas, index=False)
                mostrar_mensaje(f"✅ Excel guardado en Descargas: Cierre_Caja_{fecha_hoy}.xlsx", ft.Colors.GREEN_700)
            except Exception as ex: mostrar_mensaje(f"Error al exportar: {ex}", ft.Colors.RED_700)

        def cerrar_turno(e):
            if not movimientos_crudos: return mostrar_mensaje("No hay movimientos abiertos para cerrar.", ft.Colors.RED_700)
            try:
                ingresos = sum(m["monto"] for m in movimientos_crudos if m["tipo"] == "INGRESO")
                gastos = sum(m["monto"] for m in movimientos_crudos if m["tipo"] == "EGRESO")

                id_turno = FinanzasRepository.cerrar_turno(ingresos, gastos, movimientos_crudos, nombre_usuario)

                # Generar reporte PDF localmente (opcional/complementario)
                try:
                    from utils.generador_pdf import limpiar_texto
                    import webbrowser
                    # Podrías crear una función específica en generador_pdf si quieres un PDF hermoso
                    # Aquí lo exportamos a Excel también como resguardo
                    df = pd.DataFrame(movimientos_crudos)
                    if 'id' in df.columns: df = df.drop(columns=['id'])
                    ruta_pdf = os.path.abspath(f"Cierre_{id_turno}.csv")
                    df.to_csv(ruta_pdf, index=False)
                    webbrowser.open(f"file:///{ruta_pdf.replace(chr(92), '/')}")
                except: pass

                mostrar_mensaje(f"✅ Turno cerrado con éxito. ID: {id_turno}", ft.Colors.GREEN_700)
                cargar_flujo_caja()
            except Exception as ex: mostrar_mensaje(f"Error al cerrar turno: {ex}", ft.Colors.RED_700)

        # Contenedor 1 (A prueba de fallos de borde)
        cont_1 = ft.Container(padding=20, expand=True, content=ft.Column([
            ft.Row([
                ft.Card(content=ft.Container(padding=15, content=ft.Column([ft.Text("INGRESOS EFECTIVO", weight="bold"), t_efectivo])), expand=True),
                ft.Card(content=ft.Container(padding=15, content=ft.Column([ft.Text("INGRESOS YAPE/PLIN", weight="bold"), t_digital])), expand=True),
                ft.Card(content=ft.Container(padding=15, content=ft.Column([ft.Text("TOTAL GASTOS", weight="bold"), t_egresos])), expand=True),
                ft.Card(content=ft.Container(padding=15, bgcolor=ft.Colors.INDIGO_50, content=ft.Column([ft.Text("SALDO NETO", weight="bold", color=ft.Colors.INDIGO_900), t_neto])), expand=True)
            ]),
            ft.Divider(height=20),
            ft.Row([
                ft.Text("Detalle de Transacciones", size=18, weight="bold", color=ft.Colors.BLUE_GREY_800),
                ft.Container(expand=True),
                ft.ElevatedButton("Descargar Cierre (Excel)", icon=ft.Icons.DOWNLOAD, bgcolor=ft.Colors.GREEN_700, color="white", on_click=exportar_excel),
                ft.ElevatedButton("Cerrar Turno", icon=ft.Icons.LOCK_CLOCK, bgcolor=ft.Colors.RED_900, color="white", on_click=cerrar_turno)
            ]),
            ft.Container(content=ft.ListView([ft.Row([tabla_movimientos], scroll=ft.ScrollMode.AUTO)]), expand=True, border_radius=8, padding=10, bgcolor=ft.Colors.WHITE)
        ]))

        # ==========================================
        # TAB 2: ALERTAS DE INVENTARIO (MERMAS)
        # ==========================================
        tabla_alertas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Medicamento", weight="bold")), ft.DataColumn(ft.Text("Stock Actual", weight="bold")),
                ft.DataColumn(ft.Text("Stock Mínimo", weight="bold")), ft.DataColumn(ft.Text("Lote", weight="bold")),
                ft.DataColumn(ft.Text("Vencimiento", weight="bold")), ft.DataColumn(ft.Text("Estado", weight="bold")),
            ], rows=[]
        )

        def cargar_alertas_inventario():
            alertas = FarmaciaRepository.obtener_alertas_inventario()
            tabla_alertas.rows.clear()
            for a in alertas:
                stock = int(a.get("stock", 0))
                estado_str = "RUPTURA DE STOCK" if stock <= 0 else "STOCK CRÍTICO"
                color_estado = ft.Colors.RED_700 if stock <= 0 else ft.Colors.ORANGE_700
                tabla_alertas.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(a["medicamento"], weight="bold")), ft.DataCell(ft.Text(str(stock), color=color_estado, weight="bold")),
                    ft.DataCell(ft.Text(str(a.get("stock_minimo", 10)))), ft.DataCell(ft.Text(a.get("lote", "N/A"))),
                    ft.DataCell(ft.Text(a.get("fecha_vencimiento", "N/A"))), ft.DataCell(ft.Container(content=ft.Text(estado_str, color="white", size=11, weight="bold"), bgcolor=color_estado, padding=5, border_radius=4))
                ]))
            if page: page.update()

        # Contenedor 2 (A prueba de fallos de borde)
        cont_2 = ft.Container(padding=20, expand=True, content=ft.Column([
            ft.Text("Medicamentos en Stock Crítico o Ruptura", size=18, weight="bold", color=ft.Colors.RED_800),
            ft.Text("Estos productos requieren pedido a droguería inmediatamente.", color=ft.Colors.GREY_600), ft.Divider(height=20),
            ft.Container(content=ft.ListView([ft.Row([tabla_alertas], scroll=ft.ScrollMode.AUTO)]), expand=True, border_radius=8, padding=10, bgcolor=ft.Colors.WHITE)
        ]))

        # ==========================================
        # ENSAMBLAJE DE PESTAÑAS
        # ==========================================
        area_contenido = ft.Container(content=cont_1, expand=True, bgcolor=ft.Colors.WHITE, border_radius=10)

        def cambiar_pestana(e, indice):
            if indice == 0: cargar_flujo_caja(); area_contenido.content = cont_1
            elif indice == 1: cargar_alertas_inventario(); area_contenido.content = cont_2
            for i, btn in enumerate(botones_pestanas):
                if i == indice: btn.bgcolor, btn.color = ft.Colors.INDIGO_900, ft.Colors.WHITE
                else: btn.bgcolor, btn.color = ft.Colors.BLUE_GREY_100, ft.Colors.BLACK87
            if page: page.update()

        botones_pestanas = [
            ft.ElevatedButton("Flujo de Caja (Hoy)", icon=ft.Icons.ATTACH_MONEY, bgcolor=ft.Colors.INDIGO_900, color=ft.Colors.WHITE, on_click=lambda e: cambiar_pestana(e, 0)),
            ft.ElevatedButton("Alertas de Inventario", icon=ft.Icons.WARNING_AMBER, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: cambiar_pestana(e, 1)),
        ]

        cuerpo_principal = ft.Column([ft.Row(botones_pestanas, spacing=10), area_contenido], expand=True)

        cargar_flujo_caja()
        return ft.View(route="/reportes", appbar=barra_superior, controls=[ft.Container(content=cuerpo_principal, padding=20, expand=True, bgcolor=ft.Colors.BLUE_GREY_50)])

    except Exception as error_critico:
        return ft.View(route="/reportes", controls=[ft.Container(content=ft.Column([ft.Text(f"Error en Reportes:\n{traceback.format_exc()}")]), padding=40)])