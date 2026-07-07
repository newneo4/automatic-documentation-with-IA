"""
orchestrator.py — Orquestador del sistema de documentación (BYOA)
================================================================
Genera prompts Markdown para que tu Agente de IA local redacte la documentación.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import config
from utils.logger import setup_logger

log = setup_logger("orchestrator")

# Tareas adicionales por módulo si se requiere (ej. clickear botones antes de capturar)
MODULE_TASKS = {}

class Orchestrator:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._driver = None
        self.results = []
        
        # Ensure directories exist
        config.DOCS_PATH.mkdir(exist_ok=True)
        config.IMAGES_PATH.mkdir(exist_ok=True)
        config.SECTIONS_PATH.mkdir(exist_ok=True)
        (config.DOCS_PATH / "agent_prompts").mkdir(exist_ok=True)

    def _get_driver(self):
        """Inicializa el WebDriver y realiza el login on-demand."""
        if not self._driver:
            from skill_01_login import LoginSkill
            login_skill = LoginSkill(headless=self.headless)
            if not login_skill.login(config.USERNAME, config.PASSWORD):
                raise RuntimeError("Falló el login. Abortando orquestación.")
            self._driver = login_skill.driver
        return self._driver

    def shutdown(self):
        """Cierra el WebDriver si está abierto."""
        if self._driver:
            log.info("Cerrando navegador...")
            self._driver.quit()
            self._driver = None

    def document_module(self, module_id: str) -> dict:
        """
        Ejecuta el flujo BYOA para un módulo: Captura -> Anota -> Genera Prompt.
        """
        from skill_02_capture import CaptureSkill
        from skill_03_annotate import AnnotateSkill
        from skill_04_prompt_builder import PromptBuilder

        module = config.MODULES_BY_ID.get(module_id)
        if not module:
            raise ValueError(f"Módulo '{module_id}' no encontrado")

        log.info(f"\n{'='*60}")
        log.info(f"  ORQUESTADOR → Módulo: {module['name']}")
        log.info(f"{'='*60}")

        # 1. Capturar pantalla
        log.info("📸 Paso 1: Capturando pantalla...")
        capture_skill = CaptureSkill(driver=self._get_driver())
        img_info = capture_skill.take(module_id)
        
        # 2. Anotar imagen (cuadros rojos)
        log.info("🖌️  Paso 2: Anotando imagen...")
        annotate_skill = AnnotateSkill()
        annotated_path = annotate_skill.draw(img_info["path"], module["url"])
        
        # Usar la anotada como referencia
        if annotated_path:
            img_info["path"] = annotated_path
            # actualizamos el relative_path para usar _annotated.png
            img_info["relative_path"] = img_info["relative_path"].replace(".png", "_annotated.png")

        # 3. Construir el Prompt
        log.info("📝 Paso 3: Construyendo Prompt para el Agente...")
        builder = PromptBuilder()
        prompt_path = builder.build_prompt(
            module_name=module["name"],
            section_file=module["section_file"],
            image_relative_path=img_info["relative_path"],
            code_sources=module.get("code_sources", [])
        )

        result = {
            "module_id": module_id,
            "module_name": module["name"],
            "prompt_path": prompt_path,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        return result

    def document_all(self) -> list[dict]:
        """Documenta todos los módulos en orden."""
        log.info("🚀  Iniciando generación de prompts BYOA...")
        start = datetime.now()

        for module in config.MODULES:
            module_id = module["id"]
            try:
                self.document_module(module_id)
                log.info(f"  ✅  {module['name']} — OK")
            except Exception as e:
                log.error(f"  ❌  {module['name']} — Error: {e}")
                self.results.append({
                    "module_id": module_id,
                    "module_name": module["name"],
                    "error": str(e),
                })

        elapsed = (datetime.now() - start).seconds
        log.info(f"\n✅  Generación completada en {elapsed}s")
        return self.results


def list_modules():
    """Imprime la lista de módulos disponibles."""
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║       Módulos disponibles en project.conf                ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"  {'ID':<30} {'Nombre':<35}")
    print("  " + "─" * 65)
    for m in config.MODULES:
        print(f"  {m['id']:<30} {m['name']:<35}")
    print("╚══════════════════════════════════════════════════════════╝\n")


def main():
    parser = argparse.ArgumentParser(description="Orquestador BYOA - Generador de Prompts")
    parser.add_argument("--all", action="store_true", help="Procesar todos los módulos")
    parser.add_argument("--module", type=str, help="Procesar un módulo específico")
    parser.add_argument("--headless", action="store_true", default=True, help="Ocultar navegador (por defecto)")
    parser.add_argument("--no-headless", action="store_false", dest="headless", help="Mostrar navegador")
    parser.add_argument("--list", action="store_true", help="Listar módulos")

    args = parser.parse_args()

    if args.list:
        list_modules()
        sys.exit(0)

    if not args.all and not args.module:
        parser.print_help()
        sys.exit(1)

    orch = Orchestrator(headless=args.headless)

    try:
        if args.module:
            orch.document_module(args.module)
        elif args.all:
            orch.document_all()
            
        print(f"\n{'='*60}")
        print(f"  🤖 ¡PROMPTS GENERADOS EXITOSAMENTE!")
        print(f"{'='*60}")
        print(f"  Los archivos Markdown listos para tu IA están en:")
        print(f"  👉 docs/agent_prompts/")
        print(f"")
        print(f"  Instrucciones para continuar:")
        print(f"  1. Abre tu IDE (Cursor, Cline) o ChatGPT/Claude.")
        print(f"  2. Pásale los archivos .md generados.")
        print(f"  3. Pídele a la IA que ejecute las instrucciones en ellos.")
        print(f"  4. Cuando termine, inyecta las secciones generadas")
        print(f"     en tus archivos base (documentacion_tecnica.tex) usando")
        print(f"     \\input{{sections/XX_modulo}} y ejecuta 'make'.")
        print(f"{'='*60}\n")
            
    except Exception as e:
        log.error(f"Error crítico en la ejecución: {e}")
    finally:
        orch.shutdown()


if __name__ == "__main__":
    main()
