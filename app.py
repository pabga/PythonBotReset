# app.py (versión final con corrección de formato de secretos)

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from moodle_automator import resetear_password_moodle
# --- CAMBIO 1: Importamos la biblioteca json ---
import json

# --- Conexión a Google Sheets (adaptada para local y nube) ---
def autorizar_cliente_gspread():
    """Autoriza y devuelve un cliente de gspread, usando secretos si está en la nube."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # Comprueba si la app está corriendo en Streamlit Cloud
    if 'google_credentials' in st.secrets:
        # Lee el secreto como un bloque de texto
        creds_str = st.secrets["google_credentials"]
        # --- CAMBIO 2: Convierte el texto (string) a un diccionario ---
        creds_dict = json.loads(creds_str)
        # -----------------------------------------------------------
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else: # Si no, asume que está corriendo localmente
        creds = Credentials.from_service_account_file("google.json", scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def cargar_datos_usuarios(_client):
    """Carga los DNIs y los IDs de los usuarios."""
    spreadsheet = _client.open("Base de dato - ids").worksheet("Hoja 1")
    datos = spreadsheet.get_all_records()
    df = pd.DataFrame(datos)
    df['dni'] = df['dni'].astype(str)
    return df

@st.cache_data(ttl=300)
def cargar_credenciales_admin(_client):
    """Carga las credenciales del administrador."""
    spreadsheet = _client.open("Base de dato - ids").worksheet("Credenciales")
    admin_user = spreadsheet.acell('B1').value
    admin_pass = spreadsheet.acell('B2').value
    return admin_user, admin_pass

# --- Construcción de la Interfaz ---
st.set_page_config(page_title="Asistente Moodle", layout="centered")
st.title("🤖 Asistente de Reseteo de Contraseñas de Moodle")

try:
    gspread_client = autorizar_cliente_gspread()
    df_usuarios = cargar_datos_usuarios(gspread_client)
    admin_usuario, admin_password = cargar_credenciales_admin(gspread_client)

    st.success("Conexión con Google Drive exitosa. Credenciales de admin cargadas.")

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

except Exception as e:
    st.error(f"Error Crítico al conectar con Google Sheets o al iniciar la app: {e}")