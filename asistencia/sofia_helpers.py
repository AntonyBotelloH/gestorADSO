import os
import time
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SOFIA_PUBLIC_URL = "http://senasofiaplus.edu.co/sofia-public/"
SOFIA_INSTRUCTOR_ROLE = "13"


def create_sofia_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    return webdriver.Chrome(options=options)


def quit_sofia_driver(driver):
    try:
        driver.quit()
    except Exception:
        pass


def save_sofia_proof(driver, proof_name):
    relative_path = os.path.join('sofia_proofs', proof_name)
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    driver.save_screenshot(full_path)
    url = FileSystemStorage().url(relative_path)
    return f"{url}?t={int(time.time())}"


def login_sofia(driver, credencial):
    driver.get(SOFIA_PUBLIC_URL)
    wait = WebDriverWait(driver, 15)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'registradoBox1')))
    Select(wait.until(EC.presence_of_element_located((By.ID, 'tipoId')))).select_by_value(
        credencial.tipo_documento
    )

    input_doc = driver.find_element(By.ID, 'username')
    input_doc.clear()
    input_doc.send_keys(credencial.documento.strip())

    input_pass = driver.find_element(By.NAME, 'josso_password')
    input_pass.clear()
    input_pass.send_keys(credencial.get_password().strip())

    btn_ingresar = driver.find_element(By.NAME, 'ingresar')
    driver.execute_script("arguments[0].click();", btn_ingresar)
    return wait


def select_instructor_role(driver, wait):
    driver.switch_to.default_content()
    select_rol = wait.until(EC.presence_of_element_located((By.ID, 'seleccionRol:roles')))
    Select(select_rol).select_by_value(SOFIA_INSTRUCTOR_ROLE)
    time.sleep(3)


def navigate_to_registrar_inasistencia(driver, wait):
    btn_1 = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]")))
    driver.execute_script("arguments[0].click();", btn_1)
    time.sleep(1)
    btn_2 = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]")))
    driver.execute_script("arguments[0].click();", btn_2)
    time.sleep(1)
    btn_3 = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Registrar Inasistencia del Aprendiz')]")))
    driver.execute_script("arguments[0].click();", btn_3)
    time.sleep(3)


def navigate_to_consultar_inasistencias(driver, wait):
    btn_1 = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Gestión de Tiempos')]")))
    driver.execute_script("arguments[0].click();", btn_1)
    time.sleep(1)
    btn_2 = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Gestionar Tiempos del Instructor')]")))
    driver.execute_script("arguments[0].click();", btn_2)
    time.sleep(2)
    xpath_menu_consulta = (
        "//a[contains(text(), 'Consultar Inasistencias de Aprendices') "
        "or contains(text(), 'Consultar Inasistencia') or contains(., 'Consultar Inasistencias')]"
    )
    btn_3 = wait.until(EC.presence_of_element_located((By.XPATH, xpath_menu_consulta)))
    driver.execute_script("arguments[0].click();", btn_3)
    time.sleep(3)


def open_sofia_contenido_frame(wait):
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, 'contenido')))


def login_as_instructor(driver, credencial):
    wait = login_sofia(driver, credencial)
    select_instructor_role(driver, wait)
    return wait


def validate_sofia_credencial(request, credencial, error_session_key, message=None):
    if not credencial or not credencial.get_password():
        request.session[error_session_key] = message or 'No tienes credenciales configuradas.'
        return False
    return True


def validate_ficha_id(request, ficha_id, error_session_key, message=None):
    if not ficha_id:
        request.session[error_session_key] = message or 'Selecciona una ficha en el menú lateral.'
        return False
    return True


def run_sofia_action(request, credencial, action, success_session_key, proof_name, error_session_key=None, error_proof_name=None, success_message=None, error_message_prefix='Error en Selenium: '):
    driver = None
    try:
        driver = create_sofia_driver()
        result = action(driver)
        if success_session_key and proof_name:
            request.session[success_session_key] = save_sofia_proof(driver, proof_name)
        if success_message:
            messages.success(request, success_message)
        return result
    except Exception as e:
        if driver and success_session_key and error_proof_name:
            try:
                request.session[success_session_key] = save_sofia_proof(driver, error_proof_name)
            except Exception:
                pass
        if error_session_key:
            error_name = type(e).__name__
            error_msg = str(e).split('Stacktrace:')[0].strip()
            request.session[error_session_key] = f'{error_message_prefix} {error_name} - {error_msg[:120]}'
        return None
    finally:
        if driver:
            quit_sofia_driver(driver)


def prepare_registrar_inasistencia(driver, credencial, ficha_id):
    wait = login_as_instructor(driver, credencial)
    navigate_to_registrar_inasistencia(driver, wait)
    open_sofia_contenido_frame(wait)
    select_ficha_in_modal(wait, driver, ficha_id)
    return wait


def prepare_registrar_inasistencia_aprendiz(driver, credencial, ficha_id, documento):
    wait = login_as_instructor(driver, credencial)
    navigate_to_registrar_inasistencia(driver, wait)
    open_sofia_contenido_frame(wait)
    select_ficha_in_modal(wait, driver, ficha_id)
    select_aprendiz_in_modal(wait, driver, documento)
    return wait


def prepare_consultar_inasistencias(driver, credencial, ficha_id, documento):
    wait = login_sofia(driver, credencial)
    select_instructor_role(driver, wait)
    navigate_to_consultar_inasistencias(driver, wait)
    open_sofia_contenido_frame(wait)
    select_ficha_in_modal(wait, driver, ficha_id)
    select_aprendiz_in_modal(wait, driver, documento)
    click_consultar_button(driver, wait)
    wait_for_inasistencias_table(wait)
    return wait


def select_ficha_in_modal(wait, driver, ficha_id):
    btn_lupa = wait.until(EC.presence_of_element_located((By.ID, 'formNovedadAprendiz:fichaOLK')))
    driver.execute_script("arguments[0].click();", btn_lupa)
    time.sleep(2)
    wait.until(EC.frame_to_be_available_and_switch_to_it(
        (By.XPATH, "//iframe[contains(@src, 'modalGestionHoraCosto')]")
    ))
    btn_select = wait.until(EC.presence_of_element_located((By.XPATH, f"//tr[td[contains(., '{ficha_id}')]]//a[contains(@id, 'cmdlnkShow')]")))
    driver.execute_script("arguments[0].click();", btn_select)
    time.sleep(2)
    driver.switch_to.parent_frame()
    time.sleep(2)


def select_aprendiz_in_modal(wait, driver, documento):
    try:
        btn_aprendiz = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@id, 'aprendizOLK') or contains(@id, 'AprendizOLK')]")
        ))
        driver.execute_script('arguments[0].click();', btn_aprendiz)
        time.sleep(3)
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'viewDialog1_content')))
        try:
            input_busqueda = driver.find_element(By.XPATH, "//input[@type='text']")
            input_busqueda.clear()
            input_busqueda.send_keys(documento)
            btn_lista = driver.find_element(By.XPATH, "//a[contains(., 'Lista') or contains(., 'Consultar')]")
            driver.execute_script('arguments[0].click();', btn_lista)
            time.sleep(2)
        except Exception:
            pass

        for _ in range(15):  # Revisa hasta 15 páginas
            try:
                btn_sel = WebDriverWait(driver, 2).until(EC.presence_of_element_located(
                    (By.XPATH, f"//tr[td[contains(., '{documento}')]]//a[contains(@id, 'cmdlnkShow')]")
                ))
                driver.execute_script('arguments[0].click();', btn_sel)
                time.sleep(2)
                driver.switch_to.parent_frame()
                return
            except Exception:
                try:
                    btn_siguiente = driver.find_element(By.XPATH, "//*[contains(@title, 'Siguiente') or contains(@title, 'siguiente') or contains(@id, 'next') or contains(text(), 'Siguiente') or contains(@alt, 'Siguiente')]")
                    driver.execute_script('arguments[0].click();', btn_siguiente)
                    time.sleep(3)
                except Exception:
                    driver.switch_to.parent_frame()
                    raise Exception(f"Aprendiz con documento {documento} no encontrado en el listado.")

        driver.switch_to.parent_frame()
        raise Exception(f"Aprendiz con documento {documento} no encontrado después de 15 páginas.")

    except Exception as e:
        if "Aprendiz con documento" in str(e):
            raise e
            
        input_aprendiz = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[contains(@id, 'aprendiz') and @type='text']")
        ))
        input_aprendiz.clear()
        input_aprendiz.send_keys(documento)


def click_consultar_button(driver, wait):
    btn_consultar = wait.until(EC.presence_of_element_located((By.ID, 'formNovedadAprendiz:btnRegistrarNovedad')))
    driver.execute_script('arguments[0].click();', btn_consultar)


def wait_for_inasistencias_table(wait):
    try:
        wait.until(EC.presence_of_element_located((By.ID, 'formNovedadAprendiz:InasistenciasTable')))
    except Exception:
        pass


def clear_session_keys(request, keys):
    for key in keys:
        request.session.pop(key, None)


def click_contenido_iframe(wait):
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, 'contenido')))


def click_xpath(driver, wait, xpath):
    elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", elem)


def safe_get_text_field(driver, locator):
    element = driver.find_element(*locator)
    element.clear()
    return element


def fill_inasistencia_form(driver, fecha_str, horas_falla):
    input_fecha_ini = driver.find_element(By.ID, 'formNovedadAprendiz:fechaEjecucion')
    input_fecha_ini.clear()
    input_fecha_ini.send_keys(fecha_str)

    input_fecha_fin = driver.find_element(By.ID, 'formNovedadAprendiz:fechaFin')
    input_fecha_fin.clear()
    input_fecha_fin.send_keys(fecha_str)

    input_horas = driver.find_element(By.ID, 'formNovedadAprendiz:horasITX')
    input_horas.clear()
    input_horas.send_keys(horas_falla)

    input_justicacion = driver.find_element(By.ID, 'formNovedadAprendiz:justificacionITA')
    input_justicacion.clear()
    input_justicacion.send_keys('SIN JUSTIFICAR')


def capture_form_state(driver, registro, documento_aprendiz, sesion, suffix=None):
    from django.core.files.base import ContentFile

    png_data = driver.get_screenshot_as_png()
    nombre_archivo = f"sofia_falla_{documento_aprendiz}_{sesion.fecha}"
    if suffix:
        nombre_archivo += f"_{suffix}"
    nombre_archivo += '.png'
    registro.captura_sofia.save(nombre_archivo, ContentFile(png_data), save=True)


def click_body(driver):
    driver.find_element(By.TAG_NAME, 'body').click()


def hide_required_messages(driver):
    driver.execute_script("""
        var errores = document.querySelectorAll('.colMsgError');
        errores.forEach(function(e) { e.innerHTML = ''; });
        var textos = document.querySelectorAll('span, div, label, td');
        textos.forEach(function(t) {
            if (t.innerText && t.innerText.toLowerCase().includes('requerido')) { t.style.display = 'none'; }
        });
    """)
