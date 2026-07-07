"""
orchestrator.py — Orquestador del sistema de documentación DRII
================================================================
Coordina todos los skills para generar la documentación completa
del sistema DRII, módulo por módulo, y compila el PDF final.

Uso:
    # Documentar todos los módulos (con pausa de revisión antes de compilar)
    python orchestrator.py --all

    # Documentar todos los módulos y compilar sin pausa
    python orchestrator.py --all --auto-compile

    # Documentar un módulo específico
    python orchestrator.py --module dashboard

    # Solo generar el borrador de revisión (sin compilar PDF)
    python orchestrator.py --compile-only --review-only

    # Solo compilar el PDF (skills ya ejecutados, sin revisión)
    python orchestrator.py --compile-only --no-review

    # Listar los módulos disponibles
    python orchestrator.py --list

Argumentos:
    --all           Documentar todos los módulos
    --module ID     Documentar un módulo específico
    --headless      Navegador sin interfaz gráfica
    --compile-only  Solo compilar el PDF final (o generar draft con --review-only)
    --no-compile    No compilar el PDF al final
    --list          Listar módulos disponibles y salir
    --auto-compile  No pausar antes de compilar (omite la confirmación interactiva)
    --no-review     Saltar la generación del borrador de revisión
    --review-only   Solo generar el borrador de revisión, sin compilar PDF
"""

import subprocess
import logging
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import config

log = logging.getLogger("orchestrator")


# ==============================================================
# MAPA DE TAREAS — define qué capturas extra hacer por módulo
# Personalizar según las sub-pantallas reales de tu sistema
# ==============================================================
MODULE_TASKS = {
    # Ejemplo de configuración para capturas adicionales:
    # "login": {
    #     "extra_captures": [
    #         {
    #             "action": "Modal de recuperación de contraseña",
    #             "click_selector": "#btn-forgot-password",
    #             "wait_for_selector": ".modal-dialog",
    #             "close_selector": ".btn-close",
    #             "suffix": "-recuperar-password",
    #         }
    #     ]
    # }
}


class Orchestrator:
    """Orquestador principal del sistema de documentación DRII."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.results = []
        self.driver = None

    def _get_driver(self):
        """Reutiliza el driver entre módulos para no reiniciar el navegador."""
        if self.driver is None:
            from skill_01_login import login
            self.driver = login(headless=self.headless)
        return self.driver

    def _close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def document_module(self, module_id: str) -> dict:
        """
        Documenta un módulo usando skill_06_section_builder.

        Args:
            module_id: ID del módulo a documentar

        Returns:
            dict con resultado de la documentación
        """
        from skill_06_section_builder import SectionBuilder

        module = config.MODULES_BY_ID.get(module_id)
        if not module:
            raise ValueError(f"Módulo '{module_id}' no encontrado")

        log.info(f"\n{'='*60}")
        log.info(f"  ORQUESTADOR → Módulo: {module['name']}")
        log.info(f"{'='*60}")

        tasks = MODULE_TASKS.get(module_id, {})
        extra_captures = tasks.get("extra_captures", [])
        
        # Inject vue_sources into module and extra_captures so the describer can use them
        vue_sources = tasks.get("vue_sources", [])
        module["vue_sources"] = vue_sources
        for extra in extra_captures:
            extra["vue_sources"] = vue_sources

        builder = SectionBuilder(driver=self._get_driver())
        result = builder.build(
            module_id=module_id,
            extra_captures=extra_captures,
            write_file=True,
        )
        self.results.append(result)
        return result

    def document_all(self) -> list[dict]:
        """Documenta todos los módulos en orden."""
        log.info("🚀  Iniciando documentación completa del sistema DRII...")
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
        log.info(f"\n✅  Documentación completada en {elapsed}s")
        return self.results

    def update_main_tex_inputs(self, document_name: str = "documentacion_tecnica") -> None:
        r"""
        Actualiza el documento LaTeX principal para incluir las secciones generadas
        con \input{sections/XX_modulo} (descomentando o agregando las líneas).
        """
        main_tex = config.DOCS_PATH / f"{document_name}.tex"
        if not main_tex.exists():
            log.warning(f"No encontrado: {main_tex}")
            log.warning("¿Ejecutaste 'python scripts/init_project.py' antes de correr el orquestador? Los archivos .tex base deben existir primero.")
            return

        content = main_tex.read_text(encoding="utf-8")
        inputs_block = "\n% --- Secciones generadas por el agente ---\n"

        for module in config.MODULES:
            section_file = module.get("section_file")
            if not section_file:
                continue
            section_path = config.SECTIONS_PATH / f"{section_file}.tex"
            if section_path.exists():
                line = f"\\input{{sections/{section_file}}}"
                # Solo agregar si no existe ya
                if line not in content:
                    inputs_block += f"{line}\n"

        if inputs_block.strip() != "\n% --- Secciones generadas por el agente ---\n":
            # Insertar antes de \end{document}
            content = content.replace(
                "\\end{document}",
                f"{inputs_block}\n\\end{{document}}"
            )
            main_tex.write_text(content, encoding="utf-8")
            log.info(f"✅  {document_name}.tex actualizado con \\input{{}} de secciones.")

    def assemble_review_draft(self, document: str = "documentacion_tecnica") -> str:
        """
        Ensambla el borrador de revisión LaTeX expandiendo todos los \\input{}
        del documento principal con el contenido real de cada sección.

        El archivo resultante (docs/review/{document}_draft.tex) es prácticamente
        idéntico al que se compila a PDF y puede abrirse en cualquier editor LaTeX.

        Args:
            document: Nombre del archivo .tex principal (sin extensión).

        Returns:
            Ruta absoluta del archivo draft generado.
        """
        from skill_07_review_builder import ReviewBuilder
        builder = ReviewBuilder()
        draft_path = builder.assemble_draft(document)
        return draft_path

    def compile_pdf(self, document: str = "documentacion_tecnica") -> bool:
        """
        Compila el documento LaTeX y retorna True si tuvo éxito.

        Args:
            document: Nombre del archivo .tex (sin extensión)
        """
        log.info(f"📄  Compilando {document}.tex...")
        target = "guia" if document == "guia_usuario" else "tecnica"
        cmd = ["make", target]

        try:
            result = subprocess.run(
                cmd,
                cwd=str(config.DOCS_PATH),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=120,
            )
            if result.returncode == 0:
                log.info(f"✅  PDF generado: {document}.pdf")
                return True
            else:
                log.error(f"❌  Error de compilación:\nSTDOUT: {result.stdout[-2000:]}\nSTDERR: {result.stderr[-2000:]}")
                return False
        except subprocess.TimeoutExpired:
            log.error("❌  Timeout compilando LaTeX.")
            return False
        except FileNotFoundError:
            log.error("❌  'make' no encontrado. Compilar manualmente con: make tecnica")
            return False

    def save_report(self) -> str:
        """Guarda un reporte JSON de toda la sesión de documentación."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_modules": len(config.MODULES),
            "documented": len([r for r in self.results if "error" not in r]),
            "errors": len([r for r in self.results if "error" in r]),
            "results": self.results,
        }
        report_path = config.SKILLS_PATH / "orchestrator_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        log.info(f"📊  Reporte guardado: {report_path}")
        return str(report_path)


def list_modules():
    """Imprime la lista de módulos disponibles."""
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║       Módulos del Sistema DII disponibles                ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"  {'ID':<30} {'Nombre':<35} {'URL'}")
    print("  " + "─" * 80)
    for m in config.MODULES:
        print(f"  {m['id']:<30} {m['name']:<35} {m['url']}")
    print("╚══════════════════════════════════════════════════════════╝\n")


# ============================================================
# Punto de entrada principal
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Orquestador de documentación DRII",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true",
        help="Documentar todos los módulos del sistema")
    group.add_argument("--module", type=str,
        help="Documentar un módulo específico (por ID)")
    group.add_argument("--compile-only", action="store_true",
        help="Solo compilar el PDF o generar draft (skills ya ejecutados)")
    group.add_argument("--list", action="store_true",
        help="Listar módulos disponibles y salir")

    parser.add_argument("--headless", action="store_true",
        help="Navegador sin interfaz gráfica")
    parser.add_argument("--no-compile", action="store_true",
        help="No compilar el PDF al terminar")
    parser.add_argument("--document",
        default="documentacion_tecnica",
        help="Documento a compilar (default: documentacion_tecnica)")
    # ── Nuevos flags para el paso de revisión ───────────────────────
    parser.add_argument("--auto-compile", action="store_true",
        help="Compilar el PDF sin pausa de confirmación (útil para CI/automatización)")
    parser.add_argument("--no-review", action="store_true",
        help="Saltar la generación del borrador de revisión y compilar directamente")
    parser.add_argument("--review-only", action="store_true",
        help="Solo generar el borrador de revisión, sin compilar el PDF")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )

    if args.list:
        list_modules()
        sys.exit(0)

    orch = Orchestrator(headless=args.headless)

    try:
        if args.compile_only:
            if args.review_only:
                # Solo generar el draft de revisión
                review_path = orch.assemble_review_draft(args.document)
                print(f"\n📝  Borrador generado: {review_path}")
                sys.exit(0)
            elif args.no_review:
                # Compilar sin pasar por revisión
                success = orch.compile_pdf(args.document)
                sys.exit(0 if success else 1)
            else:
                # Comportamiento por defecto: generar draft y compilar
                success = orch.compile_pdf(args.document)
                sys.exit(0 if success else 1)

        if args.all:
            orch.document_all()
        elif args.module:
            orch.document_module(args.module)
        else:
            parser.print_help()
            sys.exit(1)

        # Actualizar \\input{} en el documento principal
        orch.update_main_tex_inputs(args.document)

        # ── PASO 4: Ensamblar borrador de revisión ──────────────────
        if not args.no_review:
            try:
                review_path = orch.assemble_review_draft(args.document)
                print(f"\n{'='*60}")
                print(f"  📝  BORRADOR DE REVISIÓN GENERADO")
                print(f"{'='*60}")
                print(f"  Archivo : {review_path}")
                print(f"  ─ Abre el archivo en tu editor y revisa el contenido LaTeX.")
                print(f"  ─ Para previsualizar: pdflatex {args.document}_draft.tex")
                print(f"  ─ Aplica las correcciones definitivas en docs/sections/")
                print(f"{'='*60}\n")
            except Exception as e:
                log.error(f"❌  Error al generar borrador de revisión: {e}")
                print("⚠   Continuando sin borrador de revisión...")

            # Si solo queríamos el draft, salir aquí
            if args.review_only:
                log.info("✋  --review-only activo: compilación omitida.")
                sys.exit(0)

            # Confirmar compilación (a menos que --auto-compile esté activo)
            if not args.auto_compile and not args.no_compile:
                print()
                try:
                    proceed = input("¿Compilar el PDF ahora? [s/N]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    proceed = ""
                if proceed != "s":
                    print("\n✋  Compilación pausada.")
                    print("    Cuando estés listo, ejecuta:")
                    print(f"      make tecnica   (para documentacion_tecnica.pdf)")
                    print(f"      make guia      (para guia_usuario.pdf)")
                    print()
                    orch.save_report()
                    sys.exit(0)

        # Compilar PDF
        if not args.no_compile and not args.review_only:
            orch.compile_pdf(args.document)

        # Reporte final
        report_path = orch.save_report()

        documented = len([r for r in orch.results if "error" not in r])
        errors = len([r for r in orch.results if "error" in r])
        print(f"\n{'='*60}")
        print(f"  DOCUMENTACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"  ✅  Módulos documentados: {documented}")
        if errors:
            print(f"  ❌  Módulos con error:    {errors}")
        print(f"  📊  Reporte: {report_path}")
        print(f"{'='*60}\n")

    finally:
        orch._close_driver()
