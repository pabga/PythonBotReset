# moodle_automator.py (versión final sin forzar cambio de contraseña)

import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def resetear_password_moodle(admin_user, admin_pass, user_id, nueva_pass):
    """
    Automatiza el reseteo de contraseña en Moodle, imitando el flujo manual
    de un administrador para máxima compatibilidad y robustez.
    """
    URL_BASE = "https://educacion.prefecturanaval.gob.ar/pev/cepa"
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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

        # --- CAMBIO: Se han comentado las siguientes dos líneas para NO forzar el cambio de contraseña ---
        # checkbox_forzar = wait.until(EC.element_to_be_clickable((By.ID, "id_preference_auth_forcepasswordchange")))
        # checkbox_forzar.click()
        # ------------------------------------------------------------------------------------------------

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