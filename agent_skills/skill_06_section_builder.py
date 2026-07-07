"""
skill_06_section_builder.py — Constructor de secciones de documentación
========================================================================
Ejecuta el flujo completo para documentar un módulo:
  1. Login en el sistema
  2. Captura de pantalla del módulo
  3. Generación de descripción
  4. Escritura del archivo .tex
  5. (Opcional) Captura de sub-pantallas adicionales

Uso independiente:
    python skill_06_section_builder.py --module dashboard
    python skill_06_section_builder.py --module semillero --headless

Cuando se importa:
    builder = SectionBuilder(driver)
    result = builder.build(module_id="dashboard")
"""

import logging
import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from skill_01_login import login
from skill_02_capture import ScreenshotCapture
from skill_03_annotate import ImageAnnotator
from skill_04_describe import ScreenDescriber
from skill_05_latex_writer import LatexWriter

log = logging.getLogger("skill_06_section_builder")


class SectionBuilder:
    """Construye una sección completa de documentación para un módulo."""

    def __init__(self, driver=None, headless: bool = False):
        """
        Args:
            driver: WebDriver autenticado. Si es None, hace login automáticamente.
            headless: Si True, inicia el navegador sin ventana (ignorado si driver!=None).
        """
        self._owns_driver = (driver is None)
        self.driver = driver or login(headless=headless)
        self.capture = ScreenshotCapture(self.driver)
        self.annotator = ImageAnnotator()
        self.describer = ScreenDescriber()
        self.writer = LatexWriter()

    def __del__(self):
        """Cierra el driver solo si fue creado por este builder."""
        if self._owns_driver and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def build(
        self,
        module_id: str,
        extra_captures: list[dict] = None,
        write_file: bool = True,
    ) -> dict:
        """
        Documenta un módulo completo.

        Args:
            module_id: ID del módulo (de config.MODULES)
            extra_captures: Lista de capturas adicionales. Cada elemento es un dict:
                {
                  "action": "navegación de pasos o descripción de la acción",
                  "url": "URL opcional (si es diferente a la del módulo)",
                  "suffix": "-formulario-nuevo",   # sufijo del archivo
                  "annotation_boxes": [(x1,y1,x2,y2), ...],  # recuadros a anotar
                }
            write_file: Si True, escribe el archivo sections/XX.tex

        Returns:
            dict con: module_id, section_file_path, captures, descriptions, latex_content
        """
        module = config.MODULES_BY_ID.get(module_id)
        if not module:
            raise ValueError(f"Módulo '{module_id}' no encontrado en config.MODULES")

        log.info(f"\n{'='*60}")
        log.info(f"  Construyendo sección: {module['name']}")
        log.info(f"{'='*60}")

        all_captures = []
        all_descriptions = []

        # ─── 1. Captura principal del módulo ────────────────────
        log.info("▶ Captura principal...")
        cap_main = self.capture.take(module_id)
        all_captures.append(cap_main)

        desc_main = self.describer.describe(
            cap_main["path"], module_id=module_id, module_name=module["name"], extra_data=module
        )
        all_descriptions.append(desc_main)

        # ─── 2. Capturas adicionales (sub-pantallas) ────────────
        if extra_captures:
            for extra in extra_captures:
                log.info(f"▶ Captura adicional: {extra.get('action', 'sin descripción')}")
                suffix = extra.get("suffix", f"-extra-{len(all_captures)}")
                url = extra.get("url", module["url"])

                if "click_selector" in extra:
                    cap_extra = self.capture.take_action(
                        url=url,
                        filename=f"{module_id}{suffix}",
                        folder=module["images_folder"],
                        click_selector=extra["click_selector"],
                        wait_for_selector=extra.get("wait_for_selector", ""),
                        close_selector=extra.get("close_selector", ""),
                        module_name=f"{module['name']} — {extra.get('action', '')}",
                    )
                else:
                    cap_extra = self.capture.take_url(
                        url=url,
                        filename=f"{module_id}{suffix}",
                        folder=module["images_folder"],
                        module_name=f"{module['name']} — {extra.get('action', '')}",
                    )

                # ─── 3. Anotaciones opcionales ───────────────────
                boxes = extra.get("annotation_boxes")
                if boxes:
                    annotated = self.annotator.add_boxes(cap_extra["path"], boxes)
                    cap_extra["path"] = annotated["annotated_path"]
                    cap_extra["relative_path"] = (
                        cap_extra["relative_path"].replace(".png", "-anotado.png")
                    )

                all_captures.append(cap_extra)

                desc_extra = self.describer.describe(
                    cap_extra["path"],
                    module_id=module_id,
                    module_name=f"{module['name']} — {extra.get('action', '')}",
                    extra_data=extra,
                )
                all_descriptions.append(desc_extra)

        # ─── 4. Escritura del archivo .tex ───────────────────────
        section_path = None
        if write_file:
            section_path = self.writer.write_section_file(
                module, all_captures, all_descriptions
            )
            log.info(f"✅  Sección completada: {section_path}")
        else:
            log.info("ℹ️   write_file=False — archivo .tex no creado.")

        # Guardar metadata de la sesión para debugging
        session_data = {
            "module_id": module_id,
            "module_name": module["name"],
            "section_file": module.get("section_file"),
            "section_file_path": section_path,
            "captures": all_captures,
            "descriptions": all_descriptions,
        }
        session_path = config.SKILLS_PATH / f"session_{module_id}.json"
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        log.info(f"ℹ️   Metadata guardada en: {session_path}")

        return session_data


# ============================================================
# Ejecución independiente
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Skill 06 — Constructor de secciones de documentación"
    )
    parser.add_argument(
        "--module", required=True,
        help=f"ID del módulo. Opciones: {[m['id'] for m in config.MODULES]}"
    )
    parser.add_argument("--headless", action="store_true",
        help="Ejecutar navegador sin interfaz gráfica")
    parser.add_argument("--no-file", action="store_true",
        help="No escribir el archivo .tex (solo capturar y describir)")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    print("=" * 60)
    print(f"  SKILL 06: Construyendo sección → {args.module}")
    print("=" * 60)

    builder = SectionBuilder(headless=args.headless)
    try:
        result = builder.build(
            module_id=args.module,
            write_file=not args.no_file,
        )
        print(f"\n✅  Sección completada:")
        print(f"   Módulo: {result['module_name']}")
        print(f"   Capturas: {len(result['captures'])}")
        if result["section_file_path"]:
            print(f"   Archivo: {result['section_file_path']}")
    except Exception as e:
        log.error(f"Error construyendo sección: {e}")
        sys.exit(1)
