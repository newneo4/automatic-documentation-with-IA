"""
skill_07_review_builder.py — Ensamblador de borrador de revisión LaTeX
============================================================================
Genera un archivo LaTeX único y autocontenido (docs/review/*_draft.tex)
expandiendo todos los \\input{sections/XX} con el contenido real de cada
archivo .tex. El resultado es prácticamente idéntico al documento que se
compila a PDF, y puede abrirse y compilarse directamente en cualquier editor.

Flujo de uso:
    1. El orquestador llama a ReviewBuilder.assemble_draft() tras generar
       todas las secciones y antes de compilar el PDF.
    2. El usuario revisa y corrige el draft en su editor preferido.
    3. Las correcciones definitivas se aplican en docs/sections/ y se
       compila el PDF final con `make tecnica` o `make guia`.

Uso independiente:
    python skill_07_review_builder.py --document guia_usuario
    python skill_07_review_builder.py --document documentacion_tecnica
"""

import re
import logging
import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

log = logging.getLogger("skill_07_review_builder")

# Cabecera que se añade al inicio de cada borrador de revisión
DRAFT_HEADER_TEMPLATE = """\
% ╔══════════════════════════════════════════════════════════════╗
% ║  BORRADOR DE REVISIÓN — GENERADO AUTOMÁTICAMENTE            ║
% ║  Proyecto : {project_name}                                   ║
% ║  Documento : {document}                                     ║
% ║  Generado  : {timestamp}                                    ║
% ║                                                              ║
% ║  INSTRUCCIONES:                                              ║
% ║  1. Revisa y corrige el contenido LaTeX en este archivo.    ║
% ║  2. Para previsualizar:                                      ║
% ║       pdflatex {document}_draft.tex  (desde docs/review/)   ║
% ║  3. Aplica las correcciones definitivas en docs/sections/   ║
% ║  4. Compila el PDF final con: make tecnica  (o make guia)   ║
% ║                                                              ║
% ║  ADVERTENCIA: Este archivo es temporal y NO se versiona.    ║
% ╚══════════════════════════════════════════════════════════════╝

"""


class ReviewBuilder:
    """
    Ensambla un documento LaTeX único de revisión expandiendo
    todos los \\input{} con el contenido real de cada sección.
    """

    def __init__(self):
        self.docs_path = config.DOCS_PATH
        self.review_path = self.docs_path / "review"

    def _expand_inputs(self, content: str, base_path: Path) -> str:
        """
        Reemplaza recursivamente cada \\input{ruta} con el contenido
        real del archivo .tex referenciado.

        Args:
            content: Contenido LaTeX a procesar.
            base_path: Directorio base para resolver rutas relativas.

        Returns:
            Contenido con todos los \\input{} expandidos.
        """
        def replace_match(match):
            raw_path = match.group(1).strip()
            # Intentar con .tex si no tiene extensión
            candidate = base_path / raw_path
            if not candidate.suffix:
                candidate = candidate.with_suffix(".tex")
            elif candidate.suffix != ".tex":
                candidate = candidate.with_suffix(".tex")

            if candidate.exists():
                log.info(f"  ↳ Expandiendo: {candidate.relative_to(self.docs_path)}")
                inner = candidate.read_text(encoding="utf-8")
                return inner + "\n"
            else:
                log.warning(f"  ⚠ Archivo no encontrado: {candidate} — se deja \\input{{}} original")
                return match.group(0)

        # Patrón que captura \input{...} con cualquier contenido dentro
        pattern = re.compile(r"\\input\{([^}]+)\}")
        return pattern.sub(replace_match, content)

    def assemble_draft(self, document: str = "guia_usuario") -> str:
        """
        Genera el archivo de borrador de revisión para un documento.

        Proceso:
          1. Lee el documento principal {document}.tex
          2. Expande inline todos los \\input{sections/XX}
          3. Añade cabecera de aviso al inicio
          4. Guarda en docs/review/{document}_draft.tex

        Args:
            document: Nombre del documento LaTeX (sin extensión).
                      Ej: "guia_usuario" o "documentacion_tecnica"

        Returns:
            Ruta absoluta del archivo draft generado.

        Raises:
            FileNotFoundError: Si el documento principal no existe.
        """
        main_tex = self.docs_path / f"{document}.tex"
        if not main_tex.exists():
            raise FileNotFoundError(f"Documento principal no encontrado: {main_tex}")

        log.info(f"📄  Leyendo documento principal: {main_tex.name}")
        content = main_tex.read_text(encoding="utf-8")

        log.info("🔗  Expandiendo secciones \\input{}...")
        expanded = self._expand_inputs(content, self.docs_path)

        # Construir cabecera con metadata de generación
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = DRAFT_HEADER_TEMPLATE.format(
            project_name=getattr(config, "PROJECT_NAME", "Proyecto Genérico"),
            document=document,
            timestamp=timestamp,
        )

        # Crear directorio review/ si no existe
        self.review_path.mkdir(parents=True, exist_ok=True)

        # Guardar el draft
        draft_file = self.review_path / f"{document}_draft.tex"
        draft_file.write_text(header + expanded, encoding="utf-8")

        size_kb = draft_file.stat().st_size / 1024
        log.info(f"✅  Draft generado: {draft_file}  ({size_kb:.1f} KB)")
        return str(draft_file)

    def assemble_all(self) -> list[str]:
        """
        Genera borradores de revisión para todos los documentos principales.

        Returns:
            Lista de rutas de archivos draft generados.
        """
        documents = ["guia_usuario", "documentacion_tecnica"]
        generated = []
        for doc in documents:
            tex_file = self.docs_path / f"{doc}.tex"
            if tex_file.exists():
                try:
                    path = self.assemble_draft(doc)
                    generated.append(path)
                except Exception as e:
                    log.error(f"❌  Error al generar draft de '{doc}': {e}")
            else:
                log.warning(f"⚠  Documento '{doc}.tex' no encontrado, omitiendo.")
        return generated


# ============================================================
# Ejecución independiente
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Skill 07 — Ensamblador de borrador de revisión LaTeX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--document",
        default="guia_usuario",
        choices=["guia_usuario", "documentacion_tecnica", "all"],
        help="Documento a ensamblar (default: guia_usuario). Use 'all' para ambos.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    builder = ReviewBuilder()

    print("\n" + "=" * 60)
    print("  SKILL 07: Ensamblador de Borrador de Revisión")
    print("=" * 60)

    try:
        if args.document == "all":
            paths = builder.assemble_all()
            print(f"\n✅  Borradores generados ({len(paths)}):")
            for p in paths:
                print(f"   → {p}")
        else:
            path = builder.assemble_draft(args.document)
            print(f"\n✅  Borrador generado:")
            print(f"   → {path}")
            print(f"\n   Puedes compilarlo con:")
            print(f"   cd docs/review && pdflatex {args.document}_draft.tex")
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error(f"Error inesperado: {e}")
        sys.exit(1)

    print()
