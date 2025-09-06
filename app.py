# app.py (versión final y refinada)

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
        # Asegúrate de que tu pestaña de datos se llame "Datos"
        spreadsheet = _client.open("Base de dato - ids").worksheet("Datos")
        datos = spreadsheet.get_all_records()
        df = pd.DataFrame(datos)
        df['dni'] = df['dni'].astype(str)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la pestaña 'Datos' en tu Google Sheet.")
        return None

@st.cache_data(ttl=300)
def cargar_credenciales_y_pass(_client):
    """Carga las credenciales del admin y la contraseña fija."""
    try:
        sheet_creds = _client.open("Base de dato - ids").worksheet("Credenciales")
        admin_user = sheet_creds.acell('B1').value
        admin_pass = sheet_creds.acell('B2').value
        
        sheet_pass = _client.open("Base de dato - ids").worksheet("Passwords")
        pass_fija = sheet_pass.acell('A1').value
        
        if not all([admin_user, admin_pass, pass_fija]):
            st.error("Error: Revisa que las pestañas 'Credenciales' y 'Passwords' tengan datos.")
            return None, None, None
            
        return admin_user, admin_pass, pass_fija
    except gspread.exceptions.WorksheetNotFound:
        st.error("Error: No se encontró la pestaña 'Credenciales' o 'Passwords'.")
        return None, None, None

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

if gspread_client:
    df_usuarios = cargar_datos_usuarios(gspread_client)
    admin_usuario, admin_password, nueva_pass_fija = cargar_credenciales_y_pass(gspread_client)

    if df_usuarios is not None and admin_usuario is not None and nueva_pass_fija is not None:
        st.success("Conexión con Google Drive exitosa. Datos cargados correctamente.")

        st.header("1. Ingresa el DNI del usuario")
        dni_a_buscar = st.text_input("DNI del usuario a restablecer")

        # --- CAMBIO 1: Se muestra la contraseña fija en el texto ---
        st.info(f"Su contraseña será reseteada a la clave fija configurada. Es: **{nueva_pass_fija}**")
        
        if st.button("🚀 Restablecer Contraseña"):
            if not dni_a_buscar:
                st.warning("Por favor, ingresa un DNI.")
            else:
                usuario_encontrado = df_usuarios[df_usuarios['dni'] == dni_a_buscar]
                if usuario_encontrado.empty:
                    st.error(f"No se encontró ningún usuario con el DNI: {dni_a_buscar}")
                else:
                    id_moodle = usuario_encontrado.iloc[0]['id']
                    # --- CAMBIO 2: Se actualiza el mensaje de carga ---
                    with st.spinner("Aguarde un momento..."):
                        exito, mensaje = resetear_password_moodle(
                            admin_usuario,
                            admin_password,
                            id_moodle,
                            nueva_pass_fija
                        )
                    if exito:
                        st.success("¡Éxito! La contraseña fue cambiada a la clave fija.")
                        st.balloons()
                    else:
                        st.error(f"Falló la automatización: {mensaje}")
    else:
        st.warning("La aplicación no puede continuar. Revisa los errores de carga de datos de Google Sheets.")

