"""
skill_02_capture.py — Motor de captura de pantallas
=====================================================================
Navega a una URL del sistema con una sesión activa y guarda
la captura de pantalla en la carpeta correcta de docs/images/.

Uso independiente:
    python skill_02_capture.py --module dashboard
    python skill_02_capture.py --module semillero
    python skill_02_capture.py --all

Cuando se importa:
    capture = ScreenshotCapture(driver)
    result = capture.take(module_id="dashboard")
    result = capture.take_url(url="...", filename="nombre", folder="modulo")
"""

import time
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

sys.path.insert(0, str(Path(__file__).parent))
import config

log = logging.getLogger("skill_02_capture")


class ScreenshotCapture:
    """Motor de capturas de pantalla del sistema."""

    def __init__(self, driver):
        """
        Args:
            driver: WebDriver autenticado (resultado de skill_01_login.login())
        """
        self.driver = driver

    def _ensure_folder(self, folder: str) -> Path:
        """Crea la subcarpeta en docs/images/ si no existe."""
        path = config.IMAGES_PATH / folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _wait_for_page_load(self, timeout: int = 10) -> None:
        """Espera a que la página esté completamente cargada."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            # Esperar a que spinners/loaders desaparezcan (si los hay)
            time.sleep(config.SCREENSHOT_WAIT)
        except Exception:
            log.warning("Timeout esperando carga de página. Continuando de todas formas.")

    def take(self, module_id: str, suffix: str = "") -> dict:
        """
        Toma captura de pantalla de un módulo registrado en config.MODULES.

        Args:
            module_id: ID del módulo (ej: "dashboard", "semillero")
            suffix: Sufijo opcional para el nombre del archivo (ej: "-formulario")

        Returns:
            dict con: path, url, module_name, filename, timestamp
        """
        module = config.MODULES_BY_ID.get(module_id)
        if not module:
            raise ValueError(f"Módulo '{module_id}' no encontrado en config.MODULES")

        return self.take_url(
            url=module["url"],
            filename=f"{module_id}{suffix}",
            folder=module["images_folder"],
            module_name=module["name"],
        )

    def take_url(
        self,
        url: str,
        filename: str,
        folder: str,
        module_name: str = "",
        scroll_to_bottom: bool = False,
    ) -> dict:
        """
        Toma captura de pantalla de una URL específica.

        Args:
            url: URL completa a capturar
            filename: Nombre del archivo (sin extensión), en kebab-case
            folder: Subcarpeta dentro de docs/images/ (ej: "dashboard")
            module_name: Nombre descriptivo del módulo (para logs)
            scroll_to_bottom: Si True, hace scroll al fondo antes de capturar

        Returns:
            dict con metadata de la captura
        """
        log.info(f"Capturando: {module_name or url}")
        log.info(f"  URL: {url}")

        # Navegar a la URL
        self.driver.get(url)
        self._wait_for_page_load()

        if scroll_to_bottom:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.3)

        # Preparar ruta de guardado
        img_folder = self._ensure_folder(folder)
        safe_filename = filename.lower().replace(" ", "-").replace("/", "-")
        file_path = img_folder / f"{safe_filename}.{config.SCREENSHOT_FORMAT}"

        # Tomar captura de pantalla
        self.driver.save_screenshot(str(file_path))
        log.info(f"  ✅ Guardada en: {file_path}")

        return {
            "path": str(file_path),
            "relative_path": f"images/{folder}/{safe_filename}.{config.SCREENSHOT_FORMAT}",
            "url": url,
            "module_name": module_name,
            "filename": safe_filename,
            "folder": folder,
            "timestamp": datetime.now().isoformat(),
            "width": config.SCREENSHOT_WIDTH,
            "height": config.SCREENSHOT_HEIGHT,
        }

    def take_action(
        self,
        url: str,
        filename: str,
        folder: str,
        click_selector: str,
        wait_for_selector: str = "",
        module_name: str = "",
        close_selector: str = "",
    ) -> dict:
        """
        Navega a una URL, hace clic en un selector CSS, espera a otro selector y toma la captura.
        """
        log.info(f"Acción en: {module_name or url}")
        log.info(f"  URL: {url}")
        log.info(f"  Clic en: {click_selector}")

        # Navegar a la URL principal
        self.driver.get(url)
        self._wait_for_page_load()

        # Hacer clic en el elemento
        try:
            by_type = By.XPATH if click_selector.startswith("//") else By.CSS_SELECTOR
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_type, click_selector))
            )
            self.driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
        except Exception as e:
            raise RuntimeError(f"Fallo al hacer clic en '{click_selector}': {e}")

        # Esperar al elemento resultante (ej. un modal)
        if wait_for_selector:
            try:
                by_type_w = By.XPATH if wait_for_selector.startswith("//") else By.CSS_SELECTOR
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by_type_w, wait_for_selector))
                )
                time.sleep(0.5) # Tiempo extra para animaciones
            except Exception as e:
                raise RuntimeError(f"Fallo al esperar '{wait_for_selector}': {e}")

        # Preparar ruta de guardado
        img_folder = self._ensure_folder(folder)
        safe_filename = filename.lower().replace(" ", "-").replace("/", "-")
        file_path = img_folder / f"{safe_filename}.{config.SCREENSHOT_FORMAT}"

        # Tomar captura de pantalla
        self.driver.save_screenshot(str(file_path))
        log.info(f"  ✅ Guardada en: {file_path}")

        # Intentar cerrar el modal si se especificó
        if close_selector:
            try:
                by_type_c = By.XPATH if close_selector.startswith("//") else By.CSS_SELECTOR
                close_btn = self.driver.find_element(by_type_c, close_selector)
                self.driver.execute_script("arguments[0].click();", close_btn)
                time.sleep(0.5)
            except Exception:
                pass

        return {
            "path": str(file_path),
            "relative_path": f"images/{folder}/{safe_filename}.{config.SCREENSHOT_FORMAT}",
            "url": url,
            "module_name": module_name,
            "filename": safe_filename,
            "folder": folder,
            "timestamp": datetime.now().isoformat(),
            "width": config.SCREENSHOT_WIDTH,
            "height": config.SCREENSHOT_HEIGHT,
        }

    def take_element(
        self,
        css_selector: str,
        filename: str,
        folder: str,
        module_name: str = "",
    ) -> dict:
        """
        Toma captura solo de un elemento específico de la página.

        Args:
            css_selector: Selector CSS del elemento a capturar
            filename: Nombre del archivo resultante
            folder: Subcarpeta en docs/images/

        Returns:
            dict con metadata de la captura
        """
        from PIL import Image
        import io

        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        except Exception as e:
            raise RuntimeError(f"Elemento '{css_selector}' no encontrado: {e}")

        # Scroll al elemento
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

        # Captura completa y recorte
        screenshot_bytes = self.driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot_bytes))

        location = element.location
        size = element.size
        left = location["x"]
        top = location["y"]
        right = left + size["width"]
        bottom = top + size["height"]
        cropped = image.crop((left, top, right, bottom))

        img_folder = self._ensure_folder(folder)
        safe_filename = filename.lower().replace(" ", "-")
        file_path = img_folder / f"{safe_filename}.{config.SCREENSHOT_FORMAT}"
        cropped.save(str(file_path))
        log.info(f"  ✅ Elemento capturado en: {file_path}")

        return {
            "path": str(file_path),
            "relative_path": f"images/{folder}/{safe_filename}.{config.SCREENSHOT_FORMAT}",
            "url": self.driver.current_url,
            "module_name": module_name,
            "filename": safe_filename,
            "folder": folder,
            "timestamp": datetime.now().isoformat(),
            "element_selector": css_selector,
        }


# ============================================================
# Ejecución independiente
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill 02 — Captura de pantallas")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--module", type=str,
        help=f"ID del módulo a capturar. Opciones: {[m['id'] for m in config.MODULES]}")
    group.add_argument("--all", action="store_true",
        help="Capturar todos los módulos del sistema")
    parser.add_argument("--headless", action="store_true",
        help="Ejecutar el navegador sin interfaz gráfica")
    args = parser.parse_args()

    from skill_01_login import login

    print("=" * 60)
    print("  SKILL 02: Captura de pantallas")
    print("=" * 60)

    driver = login(headless=args.headless)
    capture = ScreenshotCapture(driver)

    try:
        if args.all:
            results = []
            for module in config.MODULES:
                result = capture.take(module["id"])
                results.append(result)
                print(f"  ✅  {module['name']} → {result['relative_path']}")
            print(f"\nTotal: {len(results)} capturas guardadas en docs/images/")
        else:
            result = capture.take(args.module)
            print(f"\n✅  Captura guardada: {result['path']}")
    finally:
        driver.quit()
