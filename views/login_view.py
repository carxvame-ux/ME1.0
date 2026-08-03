import flet as ft
import hashlib 
from database.firebase_config import db

def obtener_login_view(page: ft.Page, on_login_success):
    
    input_usuario = ft.TextField(
        label="Usuario (ID de documento)", 
        prefix_icon=ft.Icons.PERSON, 
        width=300, 
        border_radius=10
    )
    input_password = ft.TextField(
        label="Contraseña", 
        prefix_icon=ft.Icons.LOCK, 
        password=True, 
        can_reveal_password=True, 
        width=300, 
        border_radius=10
    )

    def mostrar_error(mensaje):
        try:
            snack = ft.SnackBar(content=ft.Text(mensaje, color="white", weight="bold"), bgcolor=ft.Colors.RED_700)
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except:
            pass

    def intentar_login(e):
        usr = str(input_usuario.value).strip() 
        pwd_plano = str(input_password.value).strip()

        if not usr or not pwd_plano:
            mostrar_error("Por favor, ingresa tu usuario y contraseña.")
            return

        # ENCRIPTAMOS LA CONTRASEÑA ESCRITA ANTES DE COMPARARLA
        pwd_encriptado = hashlib.sha256(pwd_plano.encode()).hexdigest()

        try:
            doc_ref = db.collection("usuarios").document(usr).get()
            
            if doc_ref.exists:
                datos_usuario = doc_ref.to_dict()
                
                # Comparamos HASH con HASH (jamás texto plano)
                if datos_usuario.get("pwd") == pwd_encriptado:
                    
                    nombre_completo = f"{datos_usuario.get('nombres', '')} {datos_usuario.get('apellidos', '')}".strip()
                    
                    usuario_sesion = {
                        "username": usr,
                        "rol": str(datos_usuario.get("rol", "")).lower(), 
                        "nombre": nombre_completo if nombre_completo else "Usuario Desconocido"
                    }
                    on_login_success(usuario_sesion)
                else:
                    mostrar_error("Contraseña incorrecta.")
            else:
                mostrar_error("El usuario no existe en la base de datos.")
                
        except Exception as ex:
            mostrar_error(f"Error de conexión con la base de datos: {ex}")

    tarjeta_login = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=40,
            width=400,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            content=ft.Column([
                ft.Icon(ft.Icons.LOCAL_HOSPITAL_ROUNDED, size=60, color=ft.Colors.BLUE_700),
                ft.Text("SISTEMA MÉDICO", size=24, weight="bold", color=ft.Colors.BLUE_900),
                ft.Text("Inicia sesión para continuar", size=14, color=ft.Colors.GREY_500),
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                input_usuario,
                input_password,
                ft.Container(height=10),
                ft.ElevatedButton(
                    content=ft.Text("Ingresar", size=16, weight="bold", color="white"),
                    bgcolor=ft.Colors.BLUE_700,
                    width=300,
                    height=50,
                    on_click=intentar_login,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )

    contenedor_centrado = ft.Row(
        controls=[
            ft.Column(
                controls=[tarjeta_login],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

    return ft.View(
        route="/login",
        padding=0,
        controls=[
            ft.Container(
                content=contenedor_centrado,
                expand=True,
                bgcolor=ft.Colors.BLUE_GREY_50
            )
        ]
    )