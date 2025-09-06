# app.py (versión con mejor manejo de errores)

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from moodle_automator import resetear_password_moodle
import json

# --- Conexión a Google Sheets ---
def autorizar_cliente_gspread():
    """Autoriza y devuelve un cliente de gspread, usando secretos si está en la nube."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    if 'google_credentials' in st.secrets:
        creds_str = st.secrets["google_credentials"]
        creds_dict = json.loads(creds_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("google.json", scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def cargar_datos_usuarios(_client):
    """Carga los DNIs y los IDs de los usuarios."""
    try:
        # Asegúrate de que tu primera pestaña se llame "Datos" o cambia el nombre aquí
        spreadsheet = _client.open("Base de dato - ids").worksheet("Datos")
        datos = spreadsheet.get_all_records()
        df = pd.DataFrame(datos)
        df['dni'] = df['dni'].astype(str)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la pestaña 'Datos' en tu Google Sheet. Por favor, verifica el nombre.")
        return None

@st.cache_data(ttl=300)
def cargar_credenciales_admin(_client):
    """Carga las credenciales del administrador."""
    try:
        spreadsheet = _client.open("Base de dato - ids").worksheet("Credenciales")
        admin_user = spreadsheet.acell('B1').value
        admin_pass = spreadsheet.acell('B2').value
        if not admin_user or not admin_pass:
            st.error("Error: Las celdas B1 o B2 en la pestaña 'Credenciales' están vacías.")
            return None, None
        return admin_user, admin_pass
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la pestaña 'Credenciales' en tu Google Sheet. Por favor, verifica el nombre (respeta mayúsculas).")
        return None, None

# --- Construcción de la Interfaz ---
st.set_page_config(page_title="Asistente Moodle", layout="centered")
st.title("🤖 Asistente de Reseteo de Contraseñas de Moodle")

gspread_client = None
admin_usuario = None
df_usuarios = None

try:
    gspread_client = autorizar_cliente_gspread()
except Exception as e:
    st.error(f"Error Crítico en la autenticación con Google: {e}")
    st.info("Verifica que el 'secreto' de Streamlit Cloud esté configurado correctamente.")

if gspread_client:
    df_usuarios = cargar_datos_usuarios(gspread_client)
    admin_usuario, admin_password = cargar_credenciales_admin(gspread_client)

    if df_usuarios is not None and admin_usuario is not None:
        st.success("Conexión con Google Drive exitosa. Datos y credenciales cargadas.")

        st.header("1. Ingresa los datos del usuario")
        dni_a_buscar = st.text_input("DNI del usuario a restablecer")

        st.info(
            """
            **Recordatorio: La contraseña temporal debe cumplir con las siguientes reglas:**
            - Al menos 8 caracteres, 1 dígito, 1 minúscula, 1 mayúscula, 1 caracter especial (*, -, #).
            """
        )
        nueva_pass = st.text_input("Nueva contraseña temporal", type="password")

        if st.button("🚀 Restablecer Contraseña"):
            if not all([dni_a_buscar, nueva_pass]):
                st.warning("Por favor, completa los campos del DNI y la nueva contraseña.")
            else:
                usuario_encontrado = df_usuarios[df_usuarios['dni'] == dni_a_buscar]
                if usuario_encontrado.empty:
                    st.error(f"No se encontró ningún usuario con el DNI: {dni_a_buscar}")
                else:
                    id_moodle = usuario_encontrado.iloc[0]['id']
                    with st.spinner(f"Iniciando reseteo... (La ejecución es en segundo plano, espera el resultado)"):
                        exito, mensaje = resetear_password_moodle(
                            admin_usuario,
                            admin_password,
                            id_moodle,
                            nueva_pass
                        )
                    if exito:
                        st.success("¡Éxito! La contraseña fue cambiada.")
                        st.info(f"La nueva contraseña temporal es: **{nueva_pass}**")
                        st.balloons()
                    else:
                        st.error(f"Falló la automatización: {mensaje}")
    else:
        st.warning("La aplicación no puede continuar porque no se cargaron todos los datos de Google Sheets. Revisa los errores de arriba.")

