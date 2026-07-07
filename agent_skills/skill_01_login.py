"""
skill_01_login.py — Autenticación en el sistema
=====================================================
Abre el navegador, navega a /login, ingresa las credenciales
y retorna el objeto driver con la sesión activa.

Uso independiente:
    python skill_01_login.py

Retorna (cuando se importa):
    driver: selenium WebDriver con sesión autenticada
"""

import time
import logging
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Agregar carpeta padre al path para importar config
sys.path.insert(0, str(Path(__file__).parent))
import config

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
log = logging.getLogger("skill_01_login")


def build_driver(headless: bool = False) -> webdriver.Chrome:
    """Construye y retorna un WebDriver de Chrome configurado."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={config.SCREENSHOT_WIDTH},{config.SCREENSHOT_HEIGHT}")
    options.add_argument("--force-device-scale-factor=1")
    # Evitar banners de "Chrome está siendo controlado por software automatizado"
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(config.SCREENSHOT_WIDTH, config.SCREENSHOT_HEIGHT)
    return driver


def login(driver: webdriver.Chrome = None, headless: bool = False) -> webdriver.Chrome:
    """
    Autentica al usuario en el sistema.

    Args:
        driver: WebDriver existente. Si es None, crea uno nuevo.
        headless: Si True, corre el navegador sin interfaz gráfica.

    Returns:
        WebDriver autenticado con la sesión activa.
    """
    if driver is None:
        driver = build_driver(headless=headless)

    log.info(f"Navegando a: {config.LOGIN_URL}")
    driver.get(config.LOGIN_URL)

    wait = WebDriverWait(driver, 15)

    # --- Esperar a que el formulario de login esté disponible ---
    try:
        # Buscar campo de email (probar selectores comunes de Vue/React)
        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='orreo']"),
            (By.CSS_SELECTOR, "input[placeholder*='suario']"),
            (By.XPATH, "//input[@type='text'][1]"),
        ]
        email_input = None
        for selector in email_selectors:
            try:
                email_input = wait.until(EC.presence_of_element_located(selector))
                log.info(f"Campo email encontrado con: {selector}")
                break
            except Exception:
                continue

        if email_input is None:
            raise RuntimeError("No se encontró el campo de email en el formulario de login.")

        email_input.clear()
        email_input.send_keys(config.EMAIL)
        log.info(f"Email ingresado: {config.EMAIL}")

        # --- Campo de contraseña ---
        password_selectors = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
        ]
        password_input = None
        for selector in password_selectors:
            try:
                password_input = driver.find_element(*selector)
                break
            except Exception:
                continue

        if password_input is None:
            raise RuntimeError("No se encontró el campo de contraseña.")

        password_input.clear()
        password_input.send_keys(config.PASSWORD)
        log.info("Contraseña ingresada.")

        # --- Botón de submit ---
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(translate(., 'INGRESAR', 'ingresar'), 'ingresar')]"),
            (By.XPATH, "//button[contains(translate(., 'LOGIN', 'login'), 'login')]"),
            (By.XPATH, "//form//button"),
        ]
        submit_btn = None
        for selector in submit_selectors:
            try:
                submit_btn = driver.find_element(*selector)
                break
            except Exception:
                continue

        if submit_btn is None:
            raise RuntimeError("No se encontró el botón de envío del formulario.")

        submit_btn.click()
        log.info("Formulario enviado. Esperando redirección...")

        # --- Verificar login exitoso (esperar a que la URL cambie) ---
        wait.until(lambda d: "/login" not in d.current_url)
        log.info(f"Login exitoso. URL actual: {driver.current_url}")
        time.sleep(config.SCREENSHOT_WAIT)  # Esperar carga de la página

    except Exception as e:
        log.error(f"Error durante el login: {e}")
        driver.save_screenshot(str(config.SKILLS_PATH / "login_error.png"))
        raise

    return driver


def logout(driver: webdriver.Chrome) -> None:
    """Cierra la sesión del sistema."""
    try:
        logout_selectors = [
            (By.XPATH, "//button[contains(., 'Salir')]"),
            (By.XPATH, "//a[contains(., 'Cerrar sesión')]"),
            (By.XPATH, "//button[contains(., 'Logout')]"),
        ]
        for selector in logout_selectors:
            try:
                btn = driver.find_element(*selector)
                btn.click()
                log.info("Sesión cerrada.")
                return
            except Exception:
                continue
        log.warning("No se encontró botón de logout. Cerrando navegador directamente.")
    finally:
        driver.quit()


# ============================================================
# Ejecución independiente — prueba de login
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  SKILL 01: Test de autenticación")
    print("=" * 60)

    driver = None
    try:
        driver = login(headless=False)
        print(f"\n✅  Login exitoso")
        print(f"   URL actual: {driver.current_url}")
        print(f"   Título: {driver.title}")
        input("\nPresiona ENTER para cerrar el navegador...")
    except Exception as e:
        print(f"\n❌  Error: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
