import flet as ft
import traceback
import pandas as pd
import os

_CATALOGO_MEMORIA = []
def _cargar_catalogo_en_memoria():
    global _CATALOGO_MEMORIA
    if _CATALOGO_MEMORIA: return 
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for nombre in ["catalogoproductos.xlsx - Catálogo.csv", "catalogoproductos.csv", "assets/data/catalogoproductos.csv"]:
        ruta_completa = os.path.join(ruta_base, nombre)
        if os.path.exists(ruta_completa):
            try: df_meds = pd.read_csv(ruta_completa, sep=";", encoding="utf-8")
            except:
                try: df_meds = pd.read_csv(ruta_completa, sep=";", encoding="latin-1")
                except: continue
            if df_meds is not None and "Nom_Prod" in df_meds.columns:
                df_meds["Nom_Prod"], df_meds["Concent"], df_meds["Nom_Form_Farm"] = df_meds["Nom_Prod"].fillna("").astype(str).str.strip(), df_meds["Concent"].fillna("").astype(str).str.strip(), df_meds["Nom_Form_Farm"].fillna("").astype(str).str.strip()
                _CATALOGO_MEMORIA = (df_meds["Nom_Prod"] + " " + df_meds["Concent"] + " - " + df_meds["Nom_Form_Farm"]).unique().tolist()
                return
    _CATALOGO_MEMORIA = ["PARACETAMOL 500 mg - Tableta", "IBUPROFENO 400 mg - Tableta", "OMEPRAZOL 20 mg - Cápsula"]

def limpiar_texto(texto):
    txt = str(texto).lower().strip()
    for a, b in {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n', '-': ' '}.items(): txt = txt.replace(a, b)
    return txt
_cargar_catalogo_en_memoria()

def obtener_farmacia_view(page: ft.Page, on_navigate):
    try:
        from repositories.farmacia_repository import FarmaciaRepository
        
        usuario = getattr(page, "usuario_actual", None)
        nombre_usuario = usuario["nombre"] if usuario else "Farmacéutico(a)"

        barra_superior = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Volver al Panel", icon_color="white", on_click=lambda _: on_navigate("/")),
            title=ft.Text(f"Farmacia Integral | {nombre_usuario}", color="white", size=18, weight="bold"),
            bgcolor=ft.Colors.ORANGE_800,
            actions=[ft.TextButton(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color="white"), ft.Text("Cerrar Sesión", color="white")]), on_click=lambda _: [setattr(page, 'usuario_actual', None), on_navigate("/login")])]
        )

        def mostrar_mensaje(texto, color=ft.Colors.GREEN_700):
            try:
                snack = ft.SnackBar(content=ft.Text(texto, color="white", weight="bold"), bgcolor=color)
                page.overlay.append(snack)
                snack.open = True
                page.update()
            except: pass

        in_busqueda_receta = ft.TextField(label="Buscar por DNI o Nombre", prefix_icon=ft.Icons.SEARCH, expand=True)
        lista_recetas_cola = ft.ListView(expand=True, spacing=10)
        estado_despacho = {"id_ticket": None, "dni": None, "nombre": None, "items": []}
        texto_pac_despacho = ft.Text("Seleccione una receta...", size=20, weight="bold", color=ft.Colors.GREY_500)
        lista_meds_despacho = ft.ListView(height=250, spacing=10)
        in_total_despacho = ft.TextField(label="Total a Cobrar (S/)", width=150, keyboard_type="number", prefix_icon=ft.Icons.MONETIZATION_ON, value="0.00")
        dp_metodo_despacho = ft.Dropdown(label="Método", options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Yape/Plin")], width=120, value="Efectivo")
        btn_cobrar_despacho = ft.ElevatedButton("Cobrar y Descontar Stock", icon=ft.Icons.POINT_OF_SALE, bgcolor=ft.Colors.GREEN_700, color="white", height=45, disabled=True)
        btn_descartar_despacho = ft.ElevatedButton("No comprará", icon=ft.Icons.CANCEL, bgcolor=ft.Colors.BLUE_GREY_400, color="white", height=45, disabled=True)

        def recalcular_total_despacho(e=None):
            in_total_despacho.value = f"{sum(float(i['cant']) * float(i['ui_precio'].value) for i in estado_despacho['items'] if i['ui_precio'].value):.2f}"
            if page: page.update()

        def limpiar_despacho():
            estado_despacho.update({"id_ticket": None, "dni": None, "nombre": None, "items": []})
            texto_pac_despacho.value, texto_pac_despacho.color = "Seleccione una receta...", ft.Colors.GREY_500
            lista_meds_despacho.controls.clear()
            in_total_despacho.value = "0.00"
            btn_cobrar_despacho.disabled = btn_descartar_despacho.disabled = True
            if page: page.update()

        def seleccionar_ticket(ticket):
            limpiar_despacho()
            estado_despacho.update({"id_ticket": ticket["id_ticket"], "dni": ticket.get("dni", "Sin DNI"), "nombre": ticket.get("nombre_paciente", "Desconocido")})
            texto_pac_despacho.value, texto_pac_despacho.color = f"Paciente: {estado_despacho['nombre']}", ft.Colors.ORANGE_900
            
            for med in ticket.get("receta", []):
                nom_med, cant_med = med.get('medicamento', ''), med.get('cantidad', 1)
                datos_inv = FarmaciaRepository.obtener_inventario_producto(nom_med)
                txt_precio = ft.TextField(label="Precio Unit.", value=f"{datos_inv.get('precio', 0.0):.2f}", width=100, keyboard_type="number", on_change=recalcular_total_despacho)
                estado_despacho["items"].append({"medicamento": nom_med, "cant": cant_med, "ui_precio": txt_precio})
                alerta_stock = ft.Text(f"⚠️ STOCK BAJO: {datos_inv.get('stock', 0)}", color=ft.Colors.RED_700, weight="bold", size=12) if datos_inv.get('stock', 0) <= datos_inv.get('stock_minimo', 10) else ft.Text(f"Stock OK: {datos_inv.get('stock', 0)}", color=ft.Colors.GREEN_700, size=11)
                lista_meds_despacho.controls.append(ft.Card(elevation=1, content=ft.Container(padding=10, content=ft.Row([ft.Icon(ft.Icons.VACCINES, color=ft.Colors.ORANGE_700), ft.Column([ft.Text(f"{cant_med}x {nom_med}", weight="bold"), ft.Text(f"Lote: {datos_inv.get('lote', 'N/A')} | Vence: {datos_inv.get('fecha_vencimiento', 'N/A')}", color=ft.Colors.GREY_600, size=11), alerta_stock], expand=True), txt_precio]))))
            
            recalcular_total_despacho()
            btn_cobrar_despacho.disabled = btn_descartar_despacho.disabled = False
            if page: page.update()

        def cargar_tickets(e=None):
            lista_recetas_cola.controls.clear()
            tickets = FarmaciaRepository.buscar_tickets_farmacia(str(in_busqueda_receta.value).strip())
            if not tickets: lista_recetas_cola.controls.append(ft.Text("No se encontraron recetas.", color=ft.Colors.GREY_500, italic=True))
            else:
                for t in tickets:
                    est = t.get("estado", "Pendiente")
                    col, icn = (ft.Colors.ORANGE_600, ft.Icons.RECEIPT) if est == "Pendiente" else (ft.Colors.GREEN_600, ft.Icons.CHECK_CIRCLE) if est == "Vendido" else (ft.Colors.GREY_500, ft.Icons.CANCEL)
                    lista_recetas_cola.controls.append(ft.Card(elevation=1, content=ft.Container(padding=10, content=ft.Row([ft.CircleAvatar(content=ft.Icon(icn, color="white", size=18), bgcolor=col), ft.Column([ft.Text(t.get("nombre_paciente", "Paciente"), size=14, weight="bold"), ft.Text(f"{est} | DNI: {t.get('dni')}", color=ft.Colors.GREY_600, size=11)], expand=True), ft.IconButton(icon=ft.Icons.ARROW_FORWARD_IOS, icon_color=col, on_click=lambda ev, tk=t: seleccionar_ticket(tk))]))))
            if page: page.update()

        def procesar_receta_venta(e):
            if not estado_despacho["id_ticket"]: return
            try:
                FarmaciaRepository.procesar_venta_farmacia(estado_despacho["dni"], estado_despacho["nombre"], in_total_despacho.value, dp_metodo_despacho.value, [{"medicamento": i["medicamento"], "cantidad": i["cant"], "precio_unitario": i["ui_precio"].value} for i in estado_despacho["items"]], id_ticket=estado_despacho["id_ticket"], estado_decision="Vendido")
                mostrar_mensaje(f"✅ Venta registrada: S/ {in_total_despacho.value}.", ft.Colors.GREEN_700)
                limpiar_despacho(); cargar_tickets()
            except Exception as ex: mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        def descartar_receta(e):
            if not estado_despacho["id_ticket"]: return
            try:
                FarmaciaRepository.procesar_venta_farmacia(estado_despacho["dni"], estado_despacho["nombre"], 0.0, "", [], id_ticket=estado_despacho["id_ticket"], estado_decision="Descartado (No compró)")
                mostrar_mensaje("Receta descartada.", ft.Colors.BLUE_GREY_600)
                limpiar_despacho(); cargar_tickets()
            except Exception as ex: mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        btn_cobrar_despacho.on_click = procesar_receta_venta
        btn_descartar_despacho.on_click = descartar_receta
        in_busqueda_receta.on_submit = cargar_tickets

        cont_1 = ft.Row([
            ft.Container(expand=4, bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, content=ft.Column([ft.Text("Buscador de Recetas", weight="bold", color=ft.Colors.ORANGE_900), ft.Row([in_busqueda_receta, ft.IconButton(icon=ft.Icons.SEARCH, on_click=cargar_tickets)]), ft.Divider(), lista_recetas_cola])),
            ft.Container(expand=6, bgcolor=ft.Colors.WHITE, padding=20, border_radius=8, content=ft.Column([texto_pac_despacho, ft.Divider(), ft.Text("Productos de la Receta:", weight="bold"), lista_meds_despacho, ft.Divider(), ft.Row([in_total_despacho, dp_metodo_despacho, ft.Container(expand=True), btn_descartar_despacho, btn_cobrar_despacho], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)]))
        ], expand=True)

        in_vd_dni, in_vd_nom = ft.TextField(label="DNI Cliente", width=150), ft.TextField(label="Nombre Cliente", expand=True)
        in_vd_buscar = ft.TextField(label="Buscar producto para vender...", expand=True)
        lista_vd_sug, tarjeta_vd_sug = ft.ListView(height=150, spacing=2), ft.Card(visible=False, elevation=4)
        tarjeta_vd_sug.content = ft.Container(content=lista_vd_sug, padding=5)
        in_vd_cant, in_vd_total, dp_vd_metodo = ft.TextField(label="Cant.", width=80, value="1"), ft.TextField(label="Total Venta (S/)", width=150, value="0.00", disabled=True), ft.Dropdown(label="Método", options=[ft.dropdown.Option("Efectivo"), ft.dropdown.Option("Yape/Plin")], width=120, value="Efectivo")
        lista_vd_carrito_ui, carrito_vd = ft.ListView(height=200, spacing=5), []

        def recalcular_total_vd(e=None):
            in_vd_total.value = f"{sum(float(i['cant']) * float(i['ui_precio'].value) for i in carrito_vd if i['ui_precio'].value):.2f}"
            if page: page.update()

        def _seleccionar_med_vd(m): in_vd_buscar.value = m; tarjeta_vd_sug.visible = False; in_vd_cant.focus(); page.update()
        def _filtrar_meds_vd(e):
            lista_vd_sug.controls.clear()
            if len(in_vd_buscar.value.strip()) > 1:
                p_clave = limpiar_texto(in_vd_buscar.value).split()
                coincidencias = [m for m in _CATALOGO_MEMORIA if all(p in limpiar_texto(m) for p in p_clave)][:10]
                if coincidencias:
                    tarjeta_vd_sug.visible = True
                    for m in coincidencias: lista_vd_sug.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.MEDICATION), title=ft.Text(m, size=13), on_click=lambda ev, med=m: _seleccionar_med_vd(med)))
                else: tarjeta_vd_sug.visible = False
            else: tarjeta_vd_sug.visible = False
            if page: page.update()

        in_vd_buscar.on_change = _filtrar_meds_vd

        def agregar_carrito_vd(e):
            if not in_vd_buscar.value.strip() or not in_vd_cant.value: return
            nom_med = in_vd_buscar.value.strip()
            datos_inv = FarmaciaRepository.obtener_inventario_producto(nom_med)
            txt_precio = ft.TextField(label="Precio", value=f"{datos_inv.get('precio', 0.0):.2f}", width=80, keyboard_type="number", on_change=recalcular_total_vd)
            item_carrito = {"medicamento": nom_med, "cant": in_vd_cant.value, "ui_precio": txt_precio}
            carrito_vd.append(item_carrito)
            
            alerta = ft.Text(f"⚠️ Stock: {datos_inv.get('stock', 0)}", color=ft.Colors.RED_700, size=11, weight="bold") if datos_inv.get("stock", 0) <= datos_inv.get("stock_minimo", 10) else ft.Text(f"Stock: {datos_inv.get('stock', 0)}", color=ft.Colors.GREY_600, size=11)
            fila_ui = ft.Row([ft.Column([ft.Text(f"{item_carrito['cant']}x {nom_med}", weight="bold"), alerta], expand=True), txt_precio, ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda ev, item=item_carrito: [carrito_vd.remove(item), lista_vd_carrito_ui.controls.remove(item["ui_row"]), recalcular_total_vd()])])
            item_carrito["ui_row"] = fila_ui
            lista_vd_carrito_ui.controls.append(fila_ui)
            in_vd_buscar.value, in_vd_cant.value, tarjeta_vd_sug.visible = "", "1", False
            recalcular_total_vd()

        def procesar_venta_directa(e):
            if not carrito_vd: return
            try:
                FarmaciaRepository.procesar_venta_farmacia(in_vd_dni.value.strip() or "00000000", in_vd_nom.value.strip() or "Público General", in_vd_total.value, dp_vd_metodo.value, [{"medicamento": i["medicamento"], "cantidad": i["cant"], "precio_unitario": i["ui_precio"].value} for i in carrito_vd], estado_decision="Vendido")
                mostrar_mensaje(f"✅ Venta Directa: S/ {in_vd_total.value}", ft.Colors.GREEN_700)
                carrito_vd.clear(); lista_vd_carrito_ui.controls.clear()
                in_vd_nom.value = in_vd_dni.value = ""; in_vd_total.value = "0.00"
                if page: page.update()
            except Exception as ex: mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        cont_2 = ft.Container(padding=20, expand=True, bgcolor=ft.Colors.WHITE, border_radius=8, content=ft.Column([ft.Row([in_vd_dni, in_vd_nom]), ft.Divider(), ft.Text("Añadir al carrito", weight="bold", color=ft.Colors.BLUE_900), ft.Column([ft.Row([in_vd_buscar, in_vd_cant, ft.ElevatedButton("Añadir", bgcolor=ft.Colors.BLUE_800, color="white", on_click=agregar_carrito_vd)]), tarjeta_vd_sug]), ft.Divider(), ft.Text("Carrito de Compras", weight="bold"), lista_vd_carrito_ui, ft.Divider(), ft.Row([in_vd_total, dp_vd_metodo, ft.Container(expand=True), ft.ElevatedButton("Cobrar Venta Libre", icon=ft.Icons.POINT_OF_SALE, bgcolor=ft.Colors.GREEN_700, color="white", height=45, on_click=procesar_venta_directa)])]))

        in_inv_buscar = ft.TextField(label="Buscar producto en el catálogo...", expand=True)
        lista_inv_sug, tarjeta_inv_sug = ft.ListView(height=150, spacing=2), ft.Card(visible=False, elevation=4)
        tarjeta_inv_sug.content = ft.Container(content=lista_inv_sug, padding=5)
        t_inv_nom, t_inv_stock_actual = ft.Text("Seleccione un producto", size=18, weight="bold", color=ft.Colors.ORANGE_900), ft.Text("Stock Actual: 0", size=16, color=ft.Colors.GREY_700)
        in_inv_add_stock, in_inv_precio, in_inv_stock_min, in_inv_lote, in_inv_venc = ft.TextField(label="Agregar (+)", width=160, value="0"), ft.TextField(label="Precio", width=120), ft.TextField(label="Stock Mínimo", width=160), ft.TextField(label="Lote", width=150), ft.TextField(label="Vencimiento", width=180)

        def _seleccionar_med_inv(med_nombre):
            in_inv_buscar.value, tarjeta_inv_sug.visible = med_nombre, False
            datos_inv = FarmaciaRepository.obtener_inventario_producto(med_nombre)
            t_inv_nom.value, t_inv_stock_actual.value = med_nombre, f"Stock Actual: {datos_inv.get('stock', 0)}"
            in_inv_precio.value, in_inv_stock_min.value, in_inv_lote.value, in_inv_venc.value, in_inv_add_stock.value = f"{datos_inv.get('precio', 0.0):.2f}", str(datos_inv.get("stock_minimo", 10)), str(datos_inv.get("lote", "")), str(datos_inv.get("fecha_vencimiento", "")), "0"
            if page: page.update()

        def _filtrar_meds_inv(e):
            lista_inv_sug.controls.clear()
            if len(in_inv_buscar.value.strip()) > 1:
                p_clave = limpiar_texto(in_inv_buscar.value).split()
                coincidencias = [m for m in _CATALOGO_MEMORIA if all(p in limpiar_texto(m) for p in p_clave)][:10]
                if coincidencias:
                    tarjeta_inv_sug.visible = True
                    for m in coincidencias: lista_inv_sug.controls.append(ft.ListTile(leading=ft.Icon(ft.Icons.INVENTORY_2), title=ft.Text(m, size=13), on_click=lambda ev, med=m: _seleccionar_med_inv(med)))
                else: tarjeta_inv_sug.visible = False
            else: tarjeta_inv_sug.visible = False
            if page: page.update()

        in_inv_buscar.on_change = _filtrar_meds_inv

        def guardar_inventario(e):
            if t_inv_nom.value == "Seleccione un producto": return
            try:
                FarmaciaRepository.actualizar_inventario_producto(t_inv_nom.value, in_inv_add_stock.value, in_inv_precio.value, in_inv_stock_min.value, in_inv_lote.value, in_inv_venc.value)
                mostrar_mensaje("¡Inventario actualizado!", ft.Colors.GREEN_700)
                _seleccionar_med_inv(t_inv_nom.value) 
            except Exception as ex: mostrar_mensaje(f"Error: {ex}", ft.Colors.RED_700)

        cont_3 = ft.Container(padding=20, expand=True, bgcolor=ft.Colors.WHITE, border_radius=8, content=ft.Column([ft.Text("Gestión Logística", weight="bold", color=ft.Colors.BLUE_900), ft.Column([in_inv_buscar, tarjeta_inv_sug]), ft.Divider(height=30), ft.Container(padding=20, bgcolor=ft.Colors.BLUE_GREY_50, border_radius=8, content=ft.Column([t_inv_nom, t_inv_stock_actual, ft.Divider(), ft.Row([in_inv_add_stock, in_inv_precio, in_inv_stock_min]), ft.Row([in_inv_lote, in_inv_venc]), ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN_700, color="white", on_click=guardar_inventario)]))]))

        area_contenido = ft.Container(content=cont_1, expand=True)
        botones_pestanas = [
            ft.ElevatedButton("Despacho", icon=ft.Icons.RECEIPT_LONG, bgcolor=ft.Colors.ORANGE_800, color=ft.Colors.WHITE, on_click=lambda e: [cargar_tickets(), setattr(area_contenido, 'content', cont_1), [setattr(b, 'bgcolor', ft.Colors.ORANGE_800 if i==0 else ft.Colors.BLUE_GREY_100) for i,b in enumerate(botones_pestanas)], [setattr(b, 'color', ft.Colors.WHITE if i==0 else ft.Colors.BLACK87) for i,b in enumerate(botones_pestanas)], page.update()]),
            ft.ElevatedButton("Venta Libre", icon=ft.Icons.STOREFRONT, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: [setattr(area_contenido, 'content', cont_2), [setattr(b, 'bgcolor', ft.Colors.ORANGE_800 if i==1 else ft.Colors.BLUE_GREY_100) for i,b in enumerate(botones_pestanas)], [setattr(b, 'color', ft.Colors.WHITE if i==1 else ft.Colors.BLACK87) for i,b in enumerate(botones_pestanas)], page.update()]),
            ft.ElevatedButton("Inventario", icon=ft.Icons.INVENTORY, bgcolor=ft.Colors.BLUE_GREY_100, color=ft.Colors.BLACK87, on_click=lambda e: [setattr(area_contenido, 'content', cont_3), [setattr(b, 'bgcolor', ft.Colors.ORANGE_800 if i==2 else ft.Colors.BLUE_GREY_100) for i,b in enumerate(botones_pestanas)], [setattr(b, 'color', ft.Colors.WHITE if i==2 else ft.Colors.BLACK87) for i,b in enumerate(botones_pestanas)], page.update()])
        ]

        cargar_tickets()
        return ft.View(route="/farmacia", appbar=barra_superior, controls=[ft.Container(content=ft.Column([ft.Row(botones_pestanas, spacing=10), area_contenido], expand=True), padding=20, expand=True, bgcolor=ft.Colors.BLUE_GREY_50)])

    except Exception as error_critico:
        return ft.View(route="/farmacia", controls=[ft.Container(content=ft.Column([ft.Text(f"Error en Farmacia:\n{traceback.format_exc()}")]), padding=40)])