# moodle_automator.py (versión para despliegue en la nube con Chromium)

import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# webdriver-manager ya no es necesario en la nube, Selenium lo gestiona
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def resetear_password_moodle(admin_user, admin_pass, user_id, nueva_pass):
    URL_BASE = "https://educacion.prefecturanaval.gob.ar/pev/cepa"
    driver = None
    try:
        # --- CAMBIOS PARA FUNCIONAR EN STREAMLIT CLOUD ---
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Le decimos a Selenium que use el servicio de Chromium que instalamos
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        # --------------------------------------------------

        wait = WebDriverWait(driver, 15)

        # 1. Iniciar sesión en Moodle
        driver.get(f"{URL_BASE}/login/index.php")
        driver.find_element(By.ID, "username").send_keys(admin_user)
        driver.find_element(By.ID, "password").send_keys(admin_pass)
        driver.find_element(By.ID, "loginbtn").click()

        # 2. Checkpoint de Login
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "userpicture")))

        # 3. Navegar a la página de edición del perfil del usuario
        url_edicion = f"{URL_BASE}/user/editadvanced.php?id={user_id}&course=1"
        driver.get(url_edicion)

        # 4. Hacer clic en el ícono del lápiz
        lapiz_editar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.fa-pencil")))
        lapiz_editar.click()

        # 5. Interactuar con los campos del formulario de contraseña
        password_input = wait.until(EC.element_to_be_clickable((By.ID, "id_newpassword")))
        password_input.clear()
        password_input.send_keys(nueva_pass)
        password_input.send_keys(Keys.RETURN)
        
        # 6. Guardar los cambios
        time.sleep(1)
        boton_guardar = wait.until(EC.element_to_be_clickable((By.ID, "id_submitbutton")))
        driver.execute_script("arguments[0].click();", boton_guardar)

        return True, "Contraseña restablecida con éxito."

    except TimeoutException:
        traceback.print_exc()
        return False, "Un elemento de la página no cargó a tiempo. Verifica la conexión o los permisos."
    except NoSuchElementException:
        traceback.print_exc()
        return False, "No se pudo encontrar un elemento. Revisa si los IDs o clases de Moodle han cambiado."
    except Exception as e:
        traceback.print_exc()
        return False, f"Ocurrió un error inesperado: {e}"
    finally:
        if driver:
            time.sleep(2)
            driver.quit()