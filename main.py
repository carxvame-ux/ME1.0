import flet as ft

# Importamos todas nuestras vistas (Microservicios visuales)
from views.dashboard_view import obtener_dashboard_view
from views.triaje_view import obtener_triaje_view
from views.farmacia_view import obtener_farmacia_view
from views.reportes_view import obtener_reportes_view
from views.historia_clinica_view import obtener_historia_clinica_view
from views.login_view import obtener_login_view

def main(page: ft.Page):
    page.title = "Sistema Médico"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # 1. Creamos la variable de sesión vacía al abrir el programa
    if not hasattr(page, "usuario_actual"):
        page.usuario_actual = None

    # 2. Atrapamos el éxito del Login y enrutamos según el rol
    def manejar_login_exitoso(usuario_sesion):
        page.usuario_actual = usuario_sesion
        rol = str(usuario_sesion.get("rol", ""))
        
        if rol == "enfermeria":
            cambiar_ruta("/triaje")
        elif rol == "farmacia":
            cambiar_ruta("/farmacia")
        else:
            # Administrador, Médico o Recepción van al Dashboard
            cambiar_ruta("/")

    # 3. Gestor principal de pantallas
    def cambiar_ruta(ruta):
        page.views.clear()

        # =======================================================
        # 🛑 GUARDIÁN DE SEGURIDAD: 
        # Si no hay usuario y quiere ir a otra parte, lo patea al login
        # =======================================================
        if page.usuario_actual is None and ruta != "/login":
            ruta = "/login"

        # =======================================================
        # EVALUACIÓN DE RUTAS
        # =======================================================
        if ruta == "/login":
            # Pasamos la función manejar_login_exitoso a tu archivo login_view
            page.views.append(obtener_login_view(page, manejar_login_exitoso))
            
        elif ruta == "/":
            page.views.append(obtener_dashboard_view(page, cambiar_ruta))
            
        elif ruta == "/triaje":
            page.views.append(obtener_triaje_view(page, cambiar_ruta))
            
        elif ruta == "/farmacia":
            page.views.append(obtener_farmacia_view(page, cambiar_ruta))
            
        elif ruta == "/reportes":
            page.views.append(obtener_reportes_view(page, cambiar_ruta))
            
        elif ruta.startswith("/paciente/") and ruta.endswith("/datos"):
            dni_extraido = ruta.split("/")[2]
            page.views.append(obtener_historia_clinica_view(page, dni_seleccionado=dni_extraido, on_navigate=cambiar_ruta))

        page.update()

    # 4. Interceptar los cambios de ruta del navegador/sistema
    def on_route_change(e):
        cambiar_ruta(e.route)

    page.on_route_change = on_route_change
    
    # 5. Forzamos la entrada inicial al Login
    cambiar_ruta("/login")

if __name__ == "__main__":
    # Usamos run() en lugar de app() para evitar el warning amarillo de deprecación
    ft.app(target=main)